"""Fase 3 - LOAD: media e pagine sul WordPress di destinazione, in modo idempotente.

Regole di sicurezza:
- lo stato (state.json) registra tutto ciò che lo strumento ha creato: si aggiorna/cancella solo quello;
- una pagina con lo stesso slug e genitore NON creata da noi blocca l'esecuzione (nessuna sovrascrittura);
- le pagine nascono in bozza; la pubblicazione è un comando separato.
"""
from __future__ import annotations

import io
import json
import logging
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

from .config import Config
from .http import TIMEOUT
from .menu import remove_menu, sync_menu
from .navsection import remove_section_nav, sync_section_nav
from .transform import transform_site
from .wp_client import WPClient, WPError

log = logging.getLogger(__name__)


# Formati che i server più datati servono come application/octet-stream (con nosniff il browser
# non li mostra): li convertiamo in JPEG prima del caricamento.
CONVERT_TO_JPEG = {"image/avif", "image/heic", "image/heif"}


def to_jpeg(content: bytes, filename: str) -> tuple[bytes, str]:
    from PIL import Image  # import pigro: serve solo per i formati da convertire

    with Image.open(io.BytesIO(content)) as img:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=88, optimize=True)
    return buf.getvalue(), str(Path(filename).with_suffix(".jpg"))


class ConflictError(WPError):
    """Sulla destinazione esiste già contenuto non creato da questa migrazione."""


@dataclass
class State:
    path: Path
    media: dict[str, dict] = field(default_factory=dict)  # URL sorgente -> {id, url}
    pages: dict[str, dict] = field(default_factory=dict)  # source_slug -> {id, link, status}
    menu: dict = field(default_factory=dict)  # {menu_id, items: {source_slug: id}, shifted: {id: ordine originale}}
    section_nav: dict = field(default_factory=dict)  # {navigation_id, block_id}

    @classmethod
    def load(cls, path: Path) -> "State":
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(path, data.get("media", {}), data.get("pages", {}), data.get("menu", {}),
                       data.get("section_nav", {}))
        return cls(path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"media": self.media, "pages": self.pages, "menu": self.menu, "section_nav": self.section_nav}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def state_path(cfg: Config) -> Path:
    return cfg.project_dir / "state.json"


def open_state(cfg: Config, client: WPClient) -> State:
    """Stato reale, oppure una copia separata in dry-run: gli esiti fittizi non devono mai
    finire nello state.json che publish/rollback/load usano per decidere cosa toccare."""
    state = State.load(state_path(cfg))
    if client.dry_run:
        state.path = cfg.project_dir / "state.dry-run.json"
    return state


def filename_from_url(url: str) -> str:
    return unquote(Path(urlparse(url).path).name)


def media_slug(filename: str) -> str:
    """Slug che WordPress assegna a un allegato dal nome file (per la deduplica)."""
    return re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-")


def preflight(cfg: Config, client: WPClient, state: State) -> dict:
    me = client.me()
    caps = me.get("capabilities", {})
    if not (caps.get("edit_pages") and caps.get("upload_files") and caps.get("publish_pages")):
        raise WPError(f"l'utente '{me.get('username')}' non può creare/pubblicare pagine o caricare file")
    if cfg.root.source_slug not in state.pages:
        existing = client.find_pages(cfg.root.target_slug, parent=0)
        if existing:
            raise ConflictError(
                f"esiste già la pagina radice '{cfg.root.target_slug}' (id {existing[0]['id']}) non creata "
                "da questa migrazione: verificare a mano prima di procedere"
            )
    return {"user": me.get("username"), "roles": me.get("roles", [])}


def find_same_media(client: WPClient, filename: str, size: int) -> dict | None:
    """Media già presente solo se coincidono nome file E dimensione in byte: un omonimo
    diverso (altro progetto, altra cartella uploads) non deve essere riusato."""
    for media in client.find_media_by_slug(media_slug(filename)):
        details = media.get("media_details") or {}
        if filename_from_url(media.get("source_url", "")) == filename and details.get("filesize") == size:
            return media
    return None


def upload_media(cfg: Config, client: WPClient, state: State, urls: set[str], source: requests.Session) -> int:
    uploaded = 0
    for url in sorted(urls):
        if url in state.media:
            continue
        filename = filename_from_url(url)
        if client.dry_run:
            fake = client.upload_media(b"", filename, "application/octet-stream")
            state.media[url] = {"id": fake["id"], "url": url, "created": True}
            uploaded += 1
            continue
        resp = source.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        match = find_same_media(client, filename, len(resp.content))
        if match is not None:
            log.info("media già presente (stesso nome e dimensione), riuso: %s (id %s)", filename, match["id"])
            state.media[url] = {"id": match["id"], "url": match["source_url"], "created": False}
            state.save()
            continue
        mime = resp.headers.get("Content-Type", "").split(";")[0] or mimetypes.guess_type(filename)[0]
        content = resp.content
        if mime in CONVERT_TO_JPEG or Path(filename).suffix.lower() in (".avif", ".heic"):
            content, filename = to_jpeg(content, filename)
            mime = "image/jpeg"
            log.info("convertito in JPEG: %s", filename)
        title = Path(filename).stem.replace("-", " ").replace("_", " ")
        media = client.upload_media(content, filename, mime or "application/octet-stream", title=title)
        state.media[url] = {"id": media["id"], "url": media["source_url"], "created": True}
        state.save()  # salvataggio incrementale: un errore a metà non perde il lavoro fatto
        uploaded += 1
        log.info("caricato %s -> id %s", filename, media["id"])
    return uploaded


def upsert_pages(cfg: Config, client: WPClient, state: State, results: dict, status: str) -> list[dict]:
    report = []
    for pmap in cfg.ordered_pages():
        res = results[pmap.source_slug]
        parent_id = state.pages[pmap.parent]["id"] if pmap.parent else 0
        data = {
            "title": res.title,
            "content": res.content,
            "slug": pmap.target_slug,
            "parent": parent_id,
            "template": cfg.template,
            "comment_status": "closed",
            "ping_status": "closed",
        }
        known = state.pages.get(pmap.source_slug)
        if known:
            data["status"] = known.get("status", status) if status == "draft" else status
            page = client.update_page(known["id"], data)
            action = "aggiornata"
        else:
            if not client.dry_run and parent_id >= 0 and client.find_pages(pmap.target_slug, parent=parent_id):
                raise ConflictError(f"pagina '{cfg.target_path(pmap.source_slug)}' già esistente e non nostra")
            page = client.create_page({**data, "status": status})
            action = "creata"
        state.pages[pmap.source_slug] = {"id": page["id"], "link": page.get("link", ""), "status": page.get("status", status)}
        state.save()
        report.append({"slug": pmap.source_slug, "id": page["id"], "action": action, "url": cfg.target_link(pmap.source_slug)})
        log.info("pagina %s: %s (id %s)", action, cfg.target_path(pmap.source_slug), page["id"])
    return report


def used_elsewhere(client: WPClient, media_url: str, own_pages: set[int]) -> bool:
    """True se il file compare in pagine/articoli che non sono nostri (es. riusato da un editor)."""
    if client.dry_run:
        return False
    name = filename_from_url(media_url)
    hits = [h["id"] for coll in ("pages", "posts") for h in client.search(coll, name)]
    return any(hit not in own_pages for hit in hits)


def prune_unused_media(client: WPClient, state: State, used: set[str]) -> list[int]:
    """Elimina i media caricati da noi che nessuna pagina usa più (es. dopo una correzione)."""
    own_pages = {entry["id"] for entry in state.pages.values()}
    removed = []
    for url, entry in list(state.media.items()):
        if url in used or not entry.get("created", False):
            continue
        if used_elsewhere(client, entry["url"], own_pages):
            log.warning("media %s usato anche fuori dalla migrazione: non lo elimino", entry["url"])
            continue
        client.delete_media(entry["id"])
        removed.append(entry["id"])
        del state.media[url]
        state.save()
        log.info("rimosso media non più usato: %s (id %s)", url, entry["id"])
    return removed


def header_media(cfg: Config) -> set[str]:
    """Media usati dalla testata del progetto (fuori dal contenuto delle pagine)."""
    header = cfg.section_nav.header if cfg.section_nav else None
    return {header.banner} if header and header.banner else set()


def load(cfg: Config, client: WPClient, source: requests.Session, status: str = "draft") -> dict:
    state = open_state(cfg, client)
    who = preflight(cfg, client, state)
    first_pass = transform_site(cfg, media_map=state.media, write=False)
    needed = set().union(*(r.media for r in first_pass.values())) | header_media(cfg)
    uploaded = upload_media(cfg, client, state, needed, source)
    section_ref = state.section_nav.get("block_id")
    final = transform_site(cfg, media_map=state.media, write=True, section_ref=section_ref)
    leftovers = sorted(u for r in final.values() for u in r.media if u not in state.media)
    if leftovers and not client.dry_run:
        raise WPError(f"media non caricati: {leftovers}")
    pages = upsert_pages(cfg, client, state, final, status)
    section = sync_section_nav(cfg, client, state)  # servono gli ID delle pagine per il menu del progetto
    if cfg.section_nav is not None and section_ref is None:
        # primo giro: il pattern è appena nato, lo inseriamo in testa alle pagine
        final = transform_site(cfg, media_map=state.media, write=True, section_ref=state.section_nav["block_id"])
        pages = upsert_pages(cfg, client, state, final, status)
    pruned = prune_unused_media(client, state, set().union(*(r.media for r in final.values())) | header_media(cfg))
    return {"user": who, "section_nav": section, "media_uploaded": uploaded, "media_pruned": pruned, "media_total": len(state.media),
            "pages": pages}


def publish(cfg: Config, client: WPClient) -> dict:
    state = open_state(cfg, client)
    if not state.pages:
        raise WPError("nessuna pagina in state.json: eseguire prima 'load'")
    out = []
    for pmap in cfg.ordered_pages():
        entry = state.pages[pmap.source_slug]
        page = client.update_page(entry["id"], {"status": "publish"})
        entry.update({"status": page.get("status", "publish"), "link": page.get("link", entry["link"])})
        state.save()
        out.append({"slug": pmap.source_slug, "id": entry["id"], "link": entry["link"]})
    # le voci di menu si creano solo con le pagine pubblicate (WordPress nasconde quelle verso bozze)
    return {"pages": out, "menu": sync_menu(cfg, client, state)}


def rollback(cfg: Config, client: WPClient, delete_media: bool = True) -> dict:
    """Cestina le pagine (figli prima) ed elimina i media caricati da questa migrazione.

    I media già presenti sulla destinazione e solo riusati (created=False) non vengono toccati.
    """
    state = open_state(cfg, client)
    own_pages = {entry["id"] for entry in state.pages.values()}
    menu = {**remove_menu(client, state), **remove_section_nav(client, state)}
    trashed = []
    for pmap in reversed(cfg.ordered_pages()):
        entry = state.pages.pop(pmap.source_slug, None)
        if entry:
            client.trash_page(entry["id"])
            trashed.append(entry["id"])
            state.save()
    removed = []
    if delete_media:
        for url, entry in list(state.media.items()):
            if not entry.get("created", False):
                continue
            if used_elsewhere(client, entry["url"], own_pages):
                log.warning("media %s usato anche fuori dalla migrazione: non lo elimino", entry["url"])
                continue
            client.delete_media(entry["id"])
            removed.append(entry["id"])
            del state.media[url]
            state.save()
    return {**menu, "pages_trashed": trashed, "media_deleted": removed}

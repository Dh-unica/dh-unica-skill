"""Client minimale per l'API REST di WordPress (wp/v2) con Application Password."""
from __future__ import annotations

import itertools
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import requests

from .http import TIMEOUT, get_all

log = logging.getLogger(__name__)


class WPError(RuntimeError):
    pass


@dataclass(frozen=True)
class Credentials:
    user: str
    password: str


CONFIG_DIR = Path("~/.config/dh-unica")  # standard DH: ~/.config/dh-unica/<servizio>.env
LEGACY_DIR = Path("~/.config/dh-wp")      # percorso delle prime versioni (ancora letto)


def default_credentials_path(ambito: str) -> Path:
    return (CONFIG_DIR / f"wp-{ambito}.env").expanduser()


def _legacy_path(path: Path) -> Path | None:
    """~/.config/dh-unica/wp-<ambito>.env -> ~/.config/dh-wp/<ambito>.env"""
    if path.parent == CONFIG_DIR.expanduser() and path.name.startswith("wp-"):
        return (LEGACY_DIR / path.name.removeprefix("wp-")).expanduser()
    return None


def load_credentials(path: Path) -> Credentials:
    """Credenziali per la destinazione.

    Ordine: variabili d'ambiente DHM_WP_USER/DHM_WP_APP_PASSWORD (CI, server), poi il file
    KEY=VALUE con WP_USER e WP_APP_PASSWORD creato da `dhmigrate login` (permessi 600).
    """
    env_user, env_password = os.environ.get("DHM_WP_USER"), os.environ.get("DHM_WP_APP_PASSWORD")
    if env_user and env_password:
        return Credentials(env_user, env_password)
    legacy = _legacy_path(path)
    if not path.exists() and legacy is not None and legacy.exists():
        log.warning("credenziali lette dal vecchio percorso %s: spostale in %s", legacy, path)
        path = legacy
    if not path.exists():
        raise WPError(f"file credenziali assente: {path}. Crealo con: python -m dhmigrate login --url <sito>")
    if path.stat().st_mode & 0o077:
        log.warning("il file credenziali %s è leggibile da altri utenti: chmod 600", path)
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    try:
        return Credentials(values["WP_USER"], values["WP_APP_PASSWORD"])
    except KeyError as exc:
        raise WPError(f"manca {exc} in {path}") from exc


def save_credentials(path: Path, url: str, creds: Credentials) -> None:
    """Scrive il file credenziali leggibile solo dall'utente (0600), senza passare dai log."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    content = f'WP_URL={url}\nWP_USER={creds.user}\nWP_APP_PASSWORD="{creds.password}"\n'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(path, 0o600)


class WPClient:
    def __init__(self, base_url: str, creds: Credentials, session: requests.Session, dry_run: bool = False):
        self.api = base_url.rstrip("/") + "/wp-json/wp/v2"
        self.session = session
        self.auth = (creds.user, creds.password)
        self.dry_run = dry_run
        self._fake_ids = itertools.count(-1, -1)

    # --- base -------------------------------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs) -> dict | list:
        resp = self.session.request(method, f"{self.api}{path}", auth=self.auth, timeout=TIMEOUT, **kwargs)
        if not resp.ok:
            try:
                detail = resp.json().get("message", resp.text[:300])
            except ValueError:
                detail = resp.text[:300]
            raise WPError(f"{method} {path} -> HTTP {resp.status_code}: {detail}")
        return resp.json()

    def _write(self, method: str, path: str, summary: str, **kwargs) -> dict:
        if self.dry_run:
            fake = next(self._fake_ids)
            log.info("[dry-run] %s %s (%s) -> id %d", method, path, summary, fake)
            status = (kwargs.get("json") or {}).get("status", "draft")
            return {"id": fake, "link": f"dry-run://{fake}", "source_url": f"dry-run://{fake}", "status": status}
        return self._request(method, path, **kwargs)

    # --- lettura ----------------------------------------------------------------------------
    def me(self) -> dict:
        return self._request("GET", "/users/me", params={"context": "edit"})

    def find_pages(self, slug: str, parent: int | None = None) -> list[dict]:
        params: dict = {"slug": slug, "status": "publish,draft,pending,private,future", "context": "edit"}
        if parent is not None:
            params["parent"] = parent
        return get_all(self.session, f"{self.api}/pages", params, auth=self.auth)

    def get_page(self, page_id: int, context: str = "edit") -> dict:
        return self._request("GET", f"/pages/{page_id}", params={"context": context})

    def search(self, collection: str, term: str) -> list[dict]:
        """Ricerca testuale (anche nell'HTML del contenuto) su pages/posts, tutti gli stati."""
        params = {"search": term, "status": "publish,draft,pending,private,future", "_fields": "id", "per_page": 100}
        return self._request("GET", f"/{collection}", params=params)

    def find_media_by_slug(self, slug: str) -> list[dict]:
        return self._request("GET", "/media", params={"slug": slug, "context": "edit"})

    # --- scrittura --------------------------------------------------------------------------
    def create_page(self, data: dict) -> dict:
        return self._write("POST", "/pages", f"crea pagina '{data.get('slug')}'", json=data)

    def update_page(self, page_id: int, data: dict) -> dict:
        return self._write("POST", f"/pages/{page_id}", f"aggiorna pagina {page_id}", json=data)

    def trash_page(self, page_id: int) -> dict:
        return self._write("DELETE", f"/pages/{page_id}", f"cestina pagina {page_id}")

    def upload_media(self, content: bytes, filename: str, mime: str, alt: str = "", title: str = "") -> dict:
        headers = {"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": mime}
        media = self._write("POST", "/media", f"carica {filename}", data=content, headers=headers)
        if alt or title:
            meta = {k: v for k, v in {"alt_text": alt, "title": title}.items() if v}
            self._write("POST", f"/media/{media['id']}", f"metadati {filename}", json=meta)
        return media

    def delete_media(self, media_id: int) -> dict:
        return self._write("DELETE", f"/media/{media_id}", f"elimina media {media_id}", params={"force": "true"})

    # --- menu -------------------------------------------------------------------------------
    def menu_locations(self) -> dict:
        return self._request("GET", "/menu-locations")

    def menu_items(self, menu_id: int) -> list[dict]:
        params = {"menus": menu_id, "context": "edit", "per_page": 100}
        return get_all(self.session, f"{self.api}/menu-items", params, auth=self.auth)

    def create_menu_item(self, data: dict) -> dict:
        return self._write("POST", "/menu-items", f"crea voce di menu '{data.get('title')}'", json=data)

    def update_menu_item(self, item_id: int, data: dict) -> dict:
        return self._write("POST", f"/menu-items/{item_id}", f"aggiorna voce di menu {item_id}", json=data)

    def delete_menu_item(self, item_id: int) -> dict:
        return self._write("DELETE", f"/menu-items/{item_id}", f"elimina voce di menu {item_id}",
                           params={"force": "true"})

    # --- navigazione di sezione (wp_navigation + pattern sincronizzati) ------------------------
    def create_navigation(self, data: dict) -> dict:
        return self._write("POST", "/navigation", f"crea menu '{data.get('title')}'", json=data)

    def update_navigation(self, nav_id: int, data: dict) -> dict:
        return self._write("POST", f"/navigation/{nav_id}", f"aggiorna menu {nav_id}", json=data)

    def delete_navigation(self, nav_id: int) -> dict:
        return self._write("DELETE", f"/navigation/{nav_id}", f"elimina menu {nav_id}", params={"force": "true"})

    def create_block(self, data: dict) -> dict:
        return self._write("POST", "/blocks", f"crea pattern '{data.get('title')}'", json=data)

    def update_block(self, block_id: int, data: dict) -> dict:
        return self._write("POST", f"/blocks/{block_id}", f"aggiorna pattern {block_id}", json=data)

    def delete_block(self, block_id: int) -> dict:
        return self._write("DELETE", f"/blocks/{block_id}", f"elimina pattern {block_id}", params={"force": "true"})


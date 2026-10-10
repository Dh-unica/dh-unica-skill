"""Ricognizione automatica: analizza sorgente e destinazione e propone la config di migrazione.

Solo letture HTTP: nessuna scrittura né sulla sorgente né sulla destinazione.
"""
from __future__ import annotations

import html as htmllib
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

from .config import API_AMBITI, DH_DOMAIN, SLUG_PROGETTO_RE
from .extract import PAGE_FIELDS, parse_site_chrome
from .http import TIMEOUT, get_all
from .menu import render_tree
from .wp_client import Credentials

# Widget Elementor che il convertitore gestisce in modo specifico
SUPPORTED_WIDGETS = {
    "heading", "text-editor", "image", "button", "icon-box", "image-box", "divider", "spacer", "video",
    "google_maps", "icon", "social-icons", "shortcode", "wpforms", "form", "contact-form-7",
}


@dataclass
class Survey:
    source_url: str
    project_slug: str
    ambito: str
    platform: str = "static"
    generator: str = ""
    builder: str = ""
    pages: list[dict] = field(default_factory=list)
    media_count: int = 0
    widgets: Counter = field(default_factory=Counter)
    chrome: dict = field(default_factory=dict)
    target: dict = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    @property
    def target_url(self) -> str:
        return f"https://{self.ambito}.{DH_DOMAIN}"

    @property
    def unsupported_widgets(self) -> list[str]:
        return sorted(w for w in self.widgets if w not in SUPPORTED_WIDGETS)


def suggest_slug(name: str) -> str:
    """Slug di progetto secondo la name convention: minuscolo, senza separatori né accenti."""
    table = str.maketrans("àáâäèéêëìíîïòóôöùúûüç", "aaaaeeeeiiiioooouuuuc")
    return re.sub(r"[^a-z0-9]", "", name.lower().translate(table))


def survey_source(sv: Survey, session: requests.Session) -> None:
    home = session.get(sv.source_url + "/", timeout=TIMEOUT)
    home.raise_for_status()
    soup = BeautifulSoup(home.text, "html.parser")
    generators = [m.get("content", "") for m in soup.find_all("meta", attrs={"name": "generator"})]
    sv.generator = "; ".join(generators)
    sv.chrome = parse_site_chrome(home.text, sv.source_url)
    title = soup.title.get_text(strip=True) if soup.title else ""
    sv.chrome["title"] = re.split(r"\s[-–|]\s", htmllib.unescape(title))[0]
    is_wp = "wp-json" in home.headers.get("Link", "") or "/wp-content/" in home.text
    if not is_wp:
        sv.platform = "static"
        sv.issues.append("sorgente non WordPress: si userà il crawler HTML (verificare a mano il contenuto estratto)")
        return
    sv.platform = "wordpress"
    sv.builder = "elementor" if "elementor" in home.text.lower() else "gutenberg/classico"
    api = f"{sv.source_url}/wp-json/wp/v2"
    try:
        sv.pages = get_all(session, f"{api}/pages", {"_fields": PAGE_FIELDS, "status": "publish"})
        media = session.get(f"{api}/media", params={"per_page": 1}, timeout=TIMEOUT)
        sv.media_count = int(media.headers.get("X-WP-Total", "0"))
        posts = session.get(f"{api}/posts", params={"per_page": 1}, timeout=TIMEOUT)
        n_posts = int(posts.headers.get("X-WP-Total", "0"))
        if n_posts:
            sv.issues.append(f"{n_posts} articoli (post): lo strumento migra solo le pagine, valutare a parte")
    except requests.RequestException as exc:
        sv.issues.append(f"API REST sorgente non accessibile ({exc}): usare type: static")
        sv.platform = "static"
        return
    for page in sv.pages:
        sv.widgets.update(t.split(".")[0] for t in re.findall(r'data-widget_type="([^"]+)"', page["content"]["rendered"]))
    if sv.unsupported_widgets:
        sv.issues.append(f"widget convertiti in modo generico (controllare a vista): {sv.unsupported_widgets}")
    if any(w in sv.widgets for w in ("wpforms", "form", "contact-form-7")):
        sv.issues.append("modulo di contatto presente: verrà sostituito da testo (notes.form_replacement)")


def survey_target(sv: Survey, session: requests.Session, creds: Credentials | None) -> None:
    api = f"{sv.target_url}/wp-json"
    try:
        info = session.get(api, timeout=TIMEOUT).json()
    except (requests.RequestException, ValueError) as exc:
        sv.issues.append(f"destinazione {sv.target_url} non raggiungibile: {exc}")
        return
    sv.target = {"name": htmllib.unescape(info.get("name", "")), "namespaces": info.get("namespaces", [])}
    existing = session.get(f"{api}/wp/v2/pages", params={"slug": sv.project_slug, "parent": 0}, timeout=TIMEOUT).json()
    if existing:
        sv.issues.append(f"CONFLITTO: esiste già /{sv.project_slug}/ sulla destinazione (id {existing[0]['id']})")
    if creds is None:
        sv.issues.append("credenziali destinazione assenti: permessi e tema non verificati")
        return
    me = session.get(f"{api}/wp/v2/users/me", params={"context": "edit"}, auth=(creds.user, creds.password), timeout=TIMEOUT)
    if not me.ok:
        sv.issues.append(f"autenticazione destinazione fallita (HTTP {me.status_code})")
        return
    data = me.json()
    sv.target["user"] = data.get("username")
    sv.target["roles"] = data.get("roles", [])
    caps = data.get("capabilities", {})
    sv.target["unfiltered_html"] = bool(caps.get("unfiltered_html"))
    if not caps.get("unfiltered_html"):
        sv.issues.append("l'utente non ha unfiltered_html: iframe (mappe) e HTML personalizzato verranno filtrati")
    auth = (creds.user, creds.password)
    try:
        locations = session.get(f"{api}/wp/v2/menu-locations", auth=auth, timeout=TIMEOUT).json()
        menu_id = (locations.get("menu-main") or {}).get("menu") or next(
            (v["menu"] for v in locations.values() if v.get("menu")), 0)
        if menu_id:
            items = session.get(f"{api}/wp/v2/menu-items", auth=auth, timeout=TIMEOUT,
                                params={"menus": menu_id, "per_page": 100, "context": "edit"}).json()
            sv.target["menu_tree"] = render_tree(items)
            sv.target["menu_location"] = next((k for k, v in locations.items() if v.get("menu") == menu_id), "")
    except (requests.RequestException, ValueError, AttributeError) as exc:
        sv.issues.append(f"menu della destinazione non leggibile: {exc}")
    theme = session.get(f"{api}/wp/v2/themes", params={"status": "active"}, auth=(creds.user, creds.password), timeout=TIMEOUT)
    if theme.ok and theme.json():
        sv.target["theme"] = theme.json()[0].get("stylesheet")


def propose_pages(sv: Survey) -> list[dict]:
    """Gerarchia proposta: home = radice; voci di menu figlie della radice; le altre pagine
    diventano figlie della prima pagina di menu che le linka (es. sottopagine raggiunte da pulsanti)."""
    if not sv.pages:
        return [{"source_slug": "home", "target_slug": sv.project_slug, "menu_label": "Home"}]
    by_link = {p["link"].rstrip("/"): p for p in sv.pages}
    home = by_link.get(sv.source_url.rstrip("/")) or sv.pages[-1]
    menu = [(m["label"], by_link.get(m["url"].rstrip("/"))) for m in sv.chrome.get("menu", [])]
    menu_slugs = {p["slug"]: label for label, p in menu if p is not None}
    proposal = [{"source_slug": home["slug"], "target_slug": sv.project_slug,
                 "title": htmllib.unescape(home["title"]["rendered"]), "menu_label": menu_slugs.get(home["slug"], "Home")}]
    ordered = [p for _, p in menu if p is not None and p["slug"] != home["slug"]]
    ordered += [p for p in sv.pages if p not in ordered and p is not home]
    for page in ordered:
        slug = page["slug"]
        parent = home["slug"]
        if slug not in menu_slugs:
            for candidate in (p for _, p in menu if p is not None and p["slug"] != home["slug"]):
                if page["link"].rstrip("/") in candidate["content"]["rendered"]:
                    parent = candidate["slug"]
                    break
        entry = {"source_slug": slug, "target_slug": slug, "parent": parent}
        if slug in menu_slugs:
            entry["menu_label"] = menu_slugs[slug]
        proposal.append(entry)
    return proposal


def build_config(sv: Survey, credentials_path: str) -> dict:
    return {
        "project": {"slug": sv.project_slug, "title": sv.chrome.get("title") or sv.project_slug, "ambito": sv.ambito},
        "source": {"url": sv.source_url, "type": sv.platform, "elementor_default_direction": "row"},
        "target": {"url": sv.target_url, "credentials": credentials_path, "template": "page-fullwidth.php"},
        "pages": propose_pages(sv),
        "partners": [
            {"name": img["alt"] or Path(urlparse(img["src"]).path).stem, "image": img["src"], "link": img["link"]}
            for img in sv.chrome.get("footer_images", []) if img["link"]
        ],
        "menu": {"location": sv.target.get("menu_location") or "menu-main", "parent": "Progetti",
                 "label": sv.chrome.get("title") or sv.project_slug},
        "notes": {"form_replacement": "Per informazioni sul progetto scrivere ai referenti indicati sopra."},
    }


def render_markdown(sv: Survey, cfg: dict) -> str:
    lines = [
        f"# Ricognizione: {sv.source_url} → {sv.target_url}/{sv.project_slug}/",
        "",
        f"- **Piattaforma sorgente:** {sv.platform} ({sv.generator or 'generator non dichiarato'})",
        f"- **Builder:** {sv.builder or '-'}",
        f"- **Pagine:** {len(sv.pages)} · **Media:** {sv.media_count}",
        f"- **Menu sorgente:** {' · '.join(m['label'] for m in sv.chrome.get('menu', [])) or '-'}",
        f"- **Destinazione:** {sv.target.get('name', '?')} · tema `{sv.target.get('theme', '?')}` · "
        f"utente `{sv.target.get('user', '?')}` {sv.target.get('roles', '')}",
        "",
        "## Widget Elementor",
        "",
        "| Widget | Occorrenze | Supporto |",
        "|---|---:|---|",
    ]
    for widget, count in sv.widgets.most_common():
        lines.append(f"| {widget} | {count} | {'specifico' if widget in SUPPORTED_WIDGETS else 'generico ⚠'} |")
    lines += ["", f"## Menu del portale (location `{sv.target.get('menu_location', '?')}`)", ""]
    lines += sv.target.get("menu_tree") or ["- non letto (servono credenziali)"]
    lines += ["", "**Posizione proposta:** sotto «Progetti», dopo l'ultimo progetto: DA CONFERMARE CON L'UTENTE."]
    lines += ["", "## Albero URL proposto", "", "| Sorgente | Destinazione |", "|---|---|"]
    parents = {p["source_slug"]: p for p in cfg["pages"]}

    def path(slug: str) -> str:
        entry = parents[slug]
        return (path(entry["parent"]) if entry.get("parent") else "/") + entry["target_slug"] + "/"

    for entry in cfg["pages"]:
        lines.append(f"| `{entry['source_slug']}` | `{path(entry['source_slug'])}` |")
    lines += ["", "## Punti di attenzione", ""]
    lines += [f"- {issue}" for issue in sv.issues] or ["- nessuno"]
    return "\n".join(lines) + "\n"


def run_survey(source_url: str, project_slug: str, ambito: str, session: requests.Session,
               creds: Credentials | None, workdir: Path, credentials_path: str) -> tuple[Survey, dict, Path]:
    if not SLUG_PROGETTO_RE.match(project_slug):
        raise ValueError(f"slug '{project_slug}' non conforme: suggerito '{suggest_slug(project_slug)}'")
    if ambito in API_AMBITI:
        raise ValueError(f"ambito '{ambito}' riservato alle API")
    sv = Survey(source_url.rstrip("/"), project_slug, ambito)
    survey_source(sv, session)
    survey_target(sv, session, creds)
    cfg = build_config(sv, credentials_path)
    out = workdir / project_slug
    out.mkdir(parents=True, exist_ok=True)
    report = out / "survey.md"
    report.write_text(render_markdown(sv, cfg), encoding="utf-8")
    (out / "config.proposta.yaml").write_text(
        yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8"
    )
    return sv, cfg, report

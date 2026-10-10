"""Fase 1 - EXTRACT: scarica contenuti, media e stili dal sito sorgente.

Output in <workdir>/<progetto>/extract/:
  pages.json, media.json, site.json, css/post-<id>.css, html/<slug>.html
"""
from __future__ import annotations

import json
import logging
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import Config
from .http import TIMEOUT, get_all

log = logging.getLogger(__name__)

PAGE_FIELDS = "id,slug,link,parent,menu_order,status,title,content,date,modified"
MEDIA_FIELDS = "id,source_url,mime_type,alt_text,title,media_details"
SKIP_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".pdf", ".zip", ".mp4", ".mp3")


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_site_chrome(html: str, base_url: str) -> dict:
    """Ricava dal tema sorgente menu principale e immagini del footer."""
    soup = BeautifulSoup(html, "html.parser")
    menu: list[dict] = []
    nav = soup.select_one("nav, .main-navigation, [class*=menu]")
    if nav is not None:
        seen: set[str] = set()
        for a in nav.find_all("a", href=True):
            label = a.get_text(" ", strip=True)
            href = urljoin(base_url, a["href"])
            if label and href not in seen and urlparse(href).netloc == urlparse(base_url).netloc:
                seen.add(href)
                menu.append({"label": label, "url": href})
    footer_images: list[dict] = []
    footer = soup.select_one("footer")
    if footer is not None:
        for img in footer.find_all("img"):
            link = img.find_parent("a")
            footer_images.append(
                {
                    "src": urljoin(base_url, img.get("src", "")),
                    "alt": img.get("alt", ""),
                    "link": link["href"] if link is not None and link.has_attr("href") else "",
                }
            )
    return {"menu": menu, "footer_images": footer_images}


def extract_wordpress(cfg: Config, session: requests.Session) -> dict:
    out = cfg.project_dir / "extract"
    api = f"{cfg.source_url}/wp-json/wp/v2"
    pages = get_all(session, f"{api}/pages", {"_fields": PAGE_FIELDS, "status": "publish"})
    media = get_all(session, f"{api}/media", {"_fields": MEDIA_FIELDS})
    log.info("sorgente: %d pagine, %d media", len(pages), len(media))
    _write_json(out / "pages.json", pages)
    _write_json(out / "media.json", media)

    css_found = 0
    for page in pages:
        css_url = f"{cfg.source_url}/wp-content/uploads/elementor/css/post-{page['id']}.css"
        resp = session.get(css_url, timeout=TIMEOUT)
        if resp.ok and "text/css" in resp.headers.get("Content-Type", "text/css"):
            (out / "css").mkdir(parents=True, exist_ok=True)
            (out / "css" / f"post-{page['id']}.css").write_text(resp.text, encoding="utf-8")
            css_found += 1
        html = session.get(page["link"], timeout=TIMEOUT)
        html.raise_for_status()
        (out / "html").mkdir(parents=True, exist_ok=True)
        (out / "html" / f"{page['slug']}.html").write_text(html.text, encoding="utf-8")

    home = next((p for p in pages if p["link"].rstrip("/") == cfg.source_url), pages[0])
    chrome = parse_site_chrome((out / "html" / f"{home['slug']}.html").read_text(), cfg.source_url)
    _write_json(out / "site.json", chrome)
    summary = {"pages": len(pages), "media": len(media), "elementor_css": css_found}
    _write_json(out / "summary.json", summary)
    return summary


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "home"
    last = path.split("/")[-1]
    return last.rsplit(".", 1)[0] if "." in last else last


def crawl_static(cfg: Config, session: requests.Session, max_pages: int = 200) -> dict:
    """Riserva per sorgenti non WordPress: crawl BFS dello stesso dominio.

    Produce pages.json con la stessa forma dell'API WP (id, slug, link, title, content).
    """
    out = cfg.project_dir / "extract"
    host = urlparse(cfg.source_url).netloc
    queue: deque[str] = deque([cfg.source_url + "/"])
    seen: set[str] = set()
    pages: list[dict] = []
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        resp = session.get(url, timeout=TIMEOUT)
        if not resp.ok or "text/html" not in resp.headers.get("Content-Type", ""):
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        main = soup.select_one("main, article, #content, .content") or soup.body
        slug = _slug_from_url(url)
        title = soup.title.get_text(strip=True) if soup.title else slug
        pages.append(
            {
                "id": len(pages) + 1,
                "slug": slug,
                "link": url,
                "parent": 0,
                "title": {"rendered": title},
                "content": {"rendered": str(main) if main else ""},
            }
        )
        (out / "html").mkdir(parents=True, exist_ok=True)
        (out / "html" / f"{slug}.html").write_text(resp.text, encoding="utf-8")
        for a in soup.find_all("a", href=True):
            link, _ = urldefrag(urljoin(url, a["href"]))
            if urlparse(link).netloc == host and not link.lower().endswith(SKIP_EXT):
                queue.append(link)
    _write_json(out / "pages.json", pages)
    _write_json(out / "media.json", [])
    home_html = (out / "html" / f"{pages[0]['slug']}.html").read_text() if pages else ""
    _write_json(out / "site.json", parse_site_chrome(home_html, cfg.source_url))
    summary = {"pages": len(pages), "media": 0, "elementor_css": 0}
    _write_json(out / "summary.json", summary)
    return summary


def extract(cfg: Config, session: requests.Session) -> dict:
    if cfg.source_type == "wordpress":
        return extract_wordpress(cfg, session)
    return crawl_static(cfg, session)

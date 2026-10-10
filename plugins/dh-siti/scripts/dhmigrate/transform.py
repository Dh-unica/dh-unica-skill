"""Fase 2 - TRANSFORM: pagine sorgente (Elementor o HTML semplice) -> blocchi Gutenberg.

Percorre l'albero Elementor (container/section/column/widget) e produce blocchi core.
Link interni e immagini vengono riscritti verso la destinazione tramite `Rewriter`.
"""
from __future__ import annotations

import html as htmllib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from . import blocks
from .config import Config
from .elementor_css import ElementorStyles, parse as parse_css
from html import escape

from .html_clean import (Rewriter, clean_inline, fragment_to_blocks, html_to_blocks, iframe_block, image_from,
                         safe_url)

log = logging.getLogger(__name__)

FORM_WIDGETS = {"wpforms", "form", "contact-form-7", "forminator", "ninja-forms", "gravityforms"}
SOCIAL = {"facebook": "Facebook", "instagram": "Instagram", "twitter": "X (Twitter)", "x.com": "X",
          "linkedin": "LinkedIn", "youtube": "YouTube", "academia.edu": "Academia.edu"}
BUTTONS_RE = re.compile(r'^<!-- wp:buttons -->\n<div class="wp-block-buttons">(.*)</div>\n<!-- /wp:buttons -->$', re.S)


@dataclass
class TransformResult:
    source_slug: str
    title: str
    content: str
    media: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


def _norm(text: str) -> str:
    return re.sub(r"\W+", " ", htmllib.unescape(text)).strip().lower()


def merge_adjacent_buttons(items: list[str]) -> list[str]:
    """Pulsanti Elementor consecutivi -> un solo blocco core/buttons."""
    out: list[str] = []
    for block in items:
        prev = BUTTONS_RE.match(out[-1]) if out else None
        cur = BUTTONS_RE.match(block)
        if prev and cur:
            out[-1] = blocks.wrap("buttons", f'<div class="wp-block-buttons">{prev.group(1)}{cur.group(1)}</div>')
        else:
            out.append(block)
    return out


def elementor_children(tag: Tag) -> list[Tag]:
    """Elementi Elementor figli diretti, saltando i wrapper tecnici (e-con-inner, ecc.)."""
    found: list[Tag] = []
    for child in tag.find_all(True, recursive=False):
        if "elementor-element" in (child.get("class") or []):
            found.append(child)
        else:
            found.extend(elementor_children(child))
    return found


class ElementorConverter:
    def __init__(self, cfg: Config, styles: ElementorStyles, rw: Rewriter, page_title: str):
        self.cfg = cfg
        self.styles = styles
        self.rw = rw
        self.page_title = _norm(page_title)
        self.first_heading_seen = False
        self.skip_divider = False  # il divisore sotto un titolo rimosso resterebbe orfano

    # --- struttura ---------------------------------------------------------------------------
    def convert(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        out: list[str] = []
        for el in elementor_children(soup):
            out.extend(self.element(el))
        return merge_adjacent_buttons(out)

    def element(self, el: Tag) -> list[str]:
        etype = el.get("data-element_type", "")
        if etype == "widget" or el.has_attr("data-widget_type"):
            return self.widget(el)
        return self.layout(el, etype)

    def layout(self, el: Tag, etype: str) -> list[str]:
        element_id = el.get("data-id", "")
        rendered = [r for r in (merge_adjacent_buttons(self.element(k)) for k in elementor_children(el)) if r]
        if etype == "section":
            direction = "row"
        elif etype == "column":
            direction = "column"
        else:
            direction = self.styles.directions.get(element_id, self.cfg.elementor_default_direction)
        if direction == "row" and len(rendered) >= 2:
            result = [blocks.columns(["\n\n".join(r) for r in rendered])]
        else:
            result = [b for r in rendered for b in r]
        background = self.styles.backgrounds.get(element_id)
        if background:
            url, media_id = self.rw.media_url(background)
            result = [blocks.cover(url, media_id, "\n\n".join(result))]
        return result

    # --- widget ------------------------------------------------------------------------------
    def widget(self, el: Tag) -> list[str]:
        wtype = el.get("data-widget_type", "").split(".")[0]
        body = el.select_one(".elementor-widget-container") or el
        handler = getattr(self, f"w_{wtype.replace('-', '_')}", None)
        if handler is not None:
            return [b for b in handler(el, body) if b]
        if wtype in FORM_WIDGETS:
            return self.form(wtype)
        self.rw.warnings.append(f"widget '{wtype}' convertito in modo generico")
        return fragment_to_blocks(body, self.rw)

    def w_heading(self, el: Tag, body: Tag) -> list[str]:
        title = body.select_one(".elementor-heading-title") or body
        inner = clean_inline(title, self.rw).strip()
        if not self.first_heading_seen:
            self.first_heading_seen = True
            if _norm(title.get_text(" ")) == self.page_title:
                self.skip_divider = True
                return []  # duplicato del titolo pagina mostrato dal tema
        level = int(title.name[1]) if re.fullmatch(r"h[1-6]", title.name or "") else 2
        return [blocks.heading(level, inner)]

    def w_text_editor(self, el: Tag, body: Tag) -> list[str]:
        return fragment_to_blocks(body, self.rw)

    def w_image(self, el: Tag, body: Tag) -> list[str]:
        img = body.find("img")
        if img is None:
            return []
        link = img.find_parent("a")
        caption = body.find("figcaption")
        return [image_from(img, self.rw, link.get("href") if link else None,
                           clean_inline(caption, self.rw) if caption else "")]

    def w_button(self, el: Tag, body: Tag) -> list[str]:
        a = body.select_one("a.elementor-button, a")
        if a is None or not a.get("href"):
            return []
        text = (a.select_one(".elementor-button-text") or a).get_text(" ", strip=True)
        return [blocks.buttons([blocks.Button(text, self.rw.link(a["href"]), a.get("target") == "_blank")])]

    def _box(self, body: Tag, prefix: str) -> list[str]:
        out: list[str] = []
        img = body.find("img")
        if img is not None:
            out.append(image_from(img, self.rw))
        title = body.select_one(f".elementor-{prefix}-title")
        if title is not None:
            inner_tag = title.find(re.compile(r"h[1-6]|span|a"))
            text = clean_inline(title, self.rw).strip()
            level = int(title.name[1]) if re.fullmatch(r"h[1-6]", title.name) else 3
            if inner_tag is not None and not text:
                text = clean_inline(inner_tag, self.rw).strip()
            if text:
                out.append(blocks.heading(level, text))
        desc = body.select_one(f".elementor-{prefix}-description")
        if desc is not None and desc.get_text(strip=True):
            out.append(blocks.paragraph(clean_inline(desc, self.rw).strip().replace("\n", "<br>")))
        return out

    def w_icon_box(self, el: Tag, body: Tag) -> list[str]:
        return self._box(body, "icon-box")

    def w_image_box(self, el: Tag, body: Tag) -> list[str]:
        return self._box(body, "image-box")

    def w_divider(self, el: Tag, body: Tag) -> list[str]:
        if self.skip_divider:
            self.skip_divider = False
            return []
        return [blocks.separator()]

    def w_spacer(self, el: Tag, body: Tag) -> list[str]:
        return []

    def w_video(self, el: Tag, body: Tag) -> list[str]:
        settings = json.loads(htmllib.unescape(el.get("data-settings", "{}")) or "{}")
        url = settings.get("youtube_url") or ""
        if url:
            return [blocks.youtube(url)]
        other = safe_url(settings.get("vimeo_url") or settings.get("dailymotion_url") or "")
        if other:
            return [blocks.paragraph(f'<a href="{other}">Guarda il video</a>')]
        hosted = (settings.get("hosted_url") or {}).get("url")
        if hosted:
            src = safe_url(self.rw.media_url(hosted)[0])
            if src:
                return [blocks.wrap("video", f'<figure class="wp-block-video"><video controls src="{src}"></video></figure>')]
        self.rw.warnings.append("widget video senza URL riconoscibile")
        return []

    def w_google_maps(self, el: Tag, body: Tag) -> list[str]:
        iframe = body.find("iframe")
        return [iframe_block(iframe, self.rw)] if iframe is not None else []

    def _social_links(self, body: Tag) -> list[str]:
        links = []
        for a in body.find_all("a", href=True):
            href = safe_url(a["href"])
            if not href:
                continue
            label = next((v for k, v in SOCIAL.items() if k in a["href"]), urlparse(a["href"]).netloc)
            links.append(f'<a href="{href}" target="_blank" rel="noreferrer noopener">{escape(label)}</a>')
        return [blocks.paragraph(" · ".join(links))] if links else []

    def w_icon(self, el: Tag, body: Tag) -> list[str]:
        return self._social_links(body)

    def w_social_icons(self, el: Tag, body: Tag) -> list[str]:
        return self._social_links(body)

    def w_shortcode(self, el: Tag, body: Tag) -> list[str]:
        if body.find("form") is not None:
            return self.form("shortcode")
        return fragment_to_blocks(body, self.rw)

    def form(self, kind: str) -> list[str]:
        self.rw.warnings.append(f"modulo '{kind}' sostituito da testo (non migrabile)")
        text = self.cfg.notes.get("form_replacement")
        return [blocks.paragraph(text)] if text else []


# --- assemblaggio pagina --------------------------------------------------------------------------

def partners_block(cfg: Config, rw: Rewriter) -> str:
    if not cfg.partners:
        return ""
    cols = []
    for partner in cfg.partners:
        url, media_id = rw.media_url(partner.image)
        cols.append(blocks.image(url, media_id, partner.name, 160, partner.link))
    return blocks.group(
        blocks.separator() + "\n\n" + blocks.heading(2, "Partner e finanziatori") + "\n\n" + blocks.columns(cols),
        "dh-minisito-partner",
    )


def make_rewriter(cfg: Config, pages: list[dict], media: list[dict], media_map: dict[str, dict]) -> Rewriter:
    link_map: dict[str, str] = {}
    for page in pages:
        try:
            link_map[page["link"].rstrip("/")] = cfg.target_link(page["slug"])
        except KeyError:
            continue  # pagina sorgente non mappata in config
    rw = Rewriter(attachments={m["id"]: m["source_url"] for m in media})

    def resolve_media(url: str) -> tuple[str, int | None]:
        hit = media_map.get(url)
        return (hit["url"], hit["id"]) if hit else (url, None)

    def resolve_link(href: str) -> str:
        parsed = urlparse(href)
        if parsed.scheme in ("mailto", "tel") or href.startswith("#"):
            return href
        if parsed.netloc and parsed.netloc.removeprefix("www.") != cfg.source_host.removeprefix("www."):
            return href
        absolute = f"{cfg.source_url}{parsed.path}" if not parsed.netloc else href.split("#")[0].split("?")[0]
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""
        if "/wp-content/uploads/" in absolute:
            return rw.media_url(absolute)[0]
        target = link_map.get(absolute.rstrip("/"))
        if target:
            return target + fragment
        rw.warnings.append(f"link interno non mappato: {href}")
        return href

    rw.media = resolve_media
    rw.link = resolve_link
    return rw


def transform_page(cfg: Config, page: dict, styles: ElementorStyles, rw: Rewriter,
                   section_ref: int | None = None) -> TransformResult:
    pmap = cfg.page(page["slug"])
    title = pmap.title or htmllib.unescape(page["title"]["rendered"])
    html = page["content"]["rendered"]
    rw.image_width = pmap.image_width
    if "data-elementor-type" in html:
        body = ElementorConverter(cfg, styles, rw, title).convert(html)
    else:
        body = merge_adjacent_buttons(html_to_blocks(html, rw))
    # navigazione: menu globale del portale (menu.py) + barra di sezione del progetto (navsection.py)
    parts = ([f'<!-- wp:block {{"ref": {section_ref}}} /-->'] if section_ref else []) + list(body)
    if pmap.parent is None:
        parts.append(partners_block(cfg, rw))
    content = "\n\n".join(p for p in parts if p)
    return TransformResult(page["slug"], title, content, set(rw.media_seen), list(dict.fromkeys(rw.warnings)))


def load_styles(extract_dir: Path, page_id: int) -> ElementorStyles:
    css = extract_dir / "css" / f"post-{page_id}.css"
    return parse_css(css.read_text(encoding="utf-8")) if css.exists() else ElementorStyles()


def transform_site(cfg: Config, media_map: dict[str, dict] | None = None, write: bool = True,
                   section_ref: int | None = None) -> dict[str, TransformResult]:
    extract_dir = cfg.project_dir / "extract"
    pages = json.loads((extract_dir / "pages.json").read_text(encoding="utf-8"))
    media = json.loads((extract_dir / "media.json").read_text(encoding="utf-8"))
    configured = {p.source_slug for p in cfg.pages}
    skipped = [p["slug"] for p in pages if p["slug"] not in configured]
    if skipped:
        log.warning("pagine sorgente non presenti in config (ignorate): %s", skipped)
    results: dict[str, TransformResult] = {}
    for page in pages:
        if page["slug"] not in configured:
            continue
        rw = make_rewriter(cfg, pages, media, media_map or {})
        results[page["slug"]] = transform_page(cfg, page, load_styles(extract_dir, page["id"]), rw, section_ref)
    missing = configured - set(results)
    if missing:
        raise ValueError(f"pagine in config ma assenti nella sorgente: {sorted(missing)}")
    if write:
        out = cfg.project_dir / "transform"
        out.mkdir(parents=True, exist_ok=True)
        for slug, res in results.items():
            (out / f"{slug}.html").write_text(res.content, encoding="utf-8")
        report = {s: {"title": r.title, "media": sorted(r.media), "warnings": r.warnings} for s, r in results.items()}
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return results

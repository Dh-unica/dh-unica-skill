"""Da frammenti HTML arbitrari (testo di Elementor, pagine statiche) a blocchi Gutenberg puliti."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urlparse

from html import escape

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from . import blocks

INLINE_KEEP = {"a", "strong", "b", "em", "i", "u", "br", "sup", "sub", "code", "s", "mark", "small"}
INLINE_UNWRAP = {"span", "font", "abbr", "cite", "label", "time", "bdi", "ins", "del", "big"}
INLINE = INLINE_KEEP | INLINE_UNWRAP | {"img"}
DROP = {"script", "style", "noscript", "svg", "button", "input", "textarea", "select", "link", "meta"}
BLANK_RE = re.compile(r"^[\s ​]*$")
TABLE_TAGS = {"table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
              "strong", "em", "b", "i", "br", "a", "p"}
SAFE_SCHEMES = ("http", "https", "mailto", "tel")
PLACEHOLDER_RE = re.compile(r"/elementor/assets/images/placeholder\.png$")


@dataclass
class Rewriter:
    """Callback per riscrivere link e immagini durante la conversione.

    link(url) -> url di destinazione
    media(url) -> (url di destinazione, id media o None)
    """

    link: Callable[[str], str] = lambda u: u
    media: Callable[[str], tuple[str, int | None]] = lambda u: (u, None)
    image_width: int | None = None  # override larghezza immagini (da config pagina)
    attachments: dict[int, str] = field(default_factory=dict)  # id media sorgente -> URL originale
    warnings: list[str] = field(default_factory=list)
    media_seen: set[str] = field(default_factory=set)

    def media_url(self, url: str, attachment_id: int | None = None) -> tuple[str, int | None]:
        """Risolve un'immagine sorgente; preferisce l'originale dell'allegato alle miniature."""
        canonical = self.attachments.get(attachment_id, url) if attachment_id else url
        self.media_seen.add(canonical)
        return self.media(canonical)


def safe_url(url: str) -> str | None:
    """URL sicura da scrivere in un attributo: schemi ammessi, ancore e percorsi relativi; None altrimenti."""
    url = url.strip()
    scheme = urlparse(url).scheme.lower()
    if scheme and scheme not in SAFE_SCHEMES:
        return None  # javascript:, data:, vbscript:, ...
    return escape(url, quote=True)


def is_blank(html: str) -> bool:
    text = re.sub(r"<br\s*/?>|<[^>]+>|&nbsp;", " ", html)
    return BLANK_RE.match(text) is not None and "<img" not in html


BLOCKISH = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "section", "article", "header"}
TRAILING_BR_RE = re.compile(r"(?:\s*<br>)+\s*$")


def clean_inline(node: Tag | NavigableString, rw: Rewriter, depth: int = 0) -> str:
    """HTML inline ripulito: solo tag semantici, nessuno stile, link riscritti.

    Un elemento di blocco annidato (es. <h2> dentro <h2>, HTML malformato di Elementor)
    viene appiattito e separato con <br> per non fondere le parole.
    """
    if depth == 0 and isinstance(node, Tag):
        return TRAILING_BR_RE.sub("", _clean_inline(node, rw, 0))
    return _clean_inline(node, rw, depth)


def _clean_inline(node: Tag | NavigableString, rw: Rewriter, depth: int) -> str:
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        return str(node).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    name = node.name
    if name in DROP:
        return ""
    inner = "".join(_clean_inline(c, rw, depth + 1) for c in node.children)
    if name == "br":
        return "<br>"
    if name == "a":
        href = node.get("href", "").strip()
        if not href:
            return inner
        href = safe_url(rw.link(href))
        if href is None:
            rw.warnings.append("link con schema non ammesso rimosso")
            return inner
        target = ' target="_blank" rel="noreferrer noopener"' if node.get("target") == "_blank" else ""
        return f'<a href="{href}"{target}>{inner}</a>' if inner.strip() else ""
    if name == "b":
        name = "strong"
    if name == "i":
        name = "em"
    if name in INLINE_KEEP:
        return f"<{name}>{inner}</{name}>" if inner.strip() else inner
    if depth > 0 and name in BLOCKISH and inner.strip():
        return inner + "<br>"
    return inner  # unwrap: span, font, div inline...


def _li_content(li: Tag, rw: Rewriter) -> str:
    parts: list[str] = []
    inline: list[str] = []
    for child in li.children:
        if isinstance(child, Tag) and child.name in ("ul", "ol"):
            parts.append("".join(inline))
            inline = []
            parts.append(list_from(child, rw))
        elif isinstance(child, Tag) and child.name == "p":
            inline.append(clean_inline(child, rw))
        else:
            inline.append(clean_inline(child, rw))
    parts.append("".join(inline))
    return "".join(parts).strip()


def list_from(tag: Tag, rw: Rewriter) -> str:
    items = [_li_content(li, rw) for li in tag.find_all("li", recursive=False)]
    return blocks.list_block([i for i in items if i], ordered=tag.name == "ol")


def image_from(img: Tag, rw: Rewriter, link: str | None = None, caption: str = "") -> str:
    src = img.get("data-src") or img.get("src") or ""
    if not src or src.startswith("data:") or PLACEHOLDER_RE.search(src):
        return ""  # immagine assente o segnaposto di un widget Elementor vuoto
    match = re.search(r"wp-image-(\d+)", " ".join(img.get("class", [])))
    url, media_id = rw.media_url(src, int(match.group(1)) if match else None)
    width = None
    try:
        declared = int(img.get("width", "0"))
        width = declared if 0 < declared <= 400 else None
    except ValueError:
        pass
    width = rw.image_width or width
    return blocks.image(url, media_id, img.get("alt", "").strip(), width, rw.link(link) if link else None, caption)


def iframe_block(iframe: Tag, rw: Rewriter) -> str:
    src = iframe.get("src") or iframe.get("data-src") or ""
    host = urlparse(src).netloc
    yt = re.search(r"youtube(?:-nocookie)?\.com/embed/([\w-]+)", src)
    if yt:
        return blocks.youtube(f"https://www.youtube.com/watch?v={yt.group(1)}")
    if urlparse(src).scheme != "https":
        rw.warnings.append(f"iframe non https scartato: {src[:80]}")
        return ""
    try:
        height = max(100, min(int(str(iframe.get("height", "450")).rstrip("px")), 2000))
    except ValueError:
        height = 450
    title = escape(iframe.get("title", host), quote=True)
    return blocks.html_block(
        f'<iframe src="{escape(src, quote=True)}" title="{title}" width="100%" height="{height}" '
        'style="border:0" loading="lazy" allowfullscreen></iframe>'
    )


def fragment_to_blocks(root: Tag, rw: Rewriter) -> list[str]:
    """Converte i figli di `root` in una lista di blocchi serializzati."""
    out: list[str] = []
    pending: list[str] = []

    def flush() -> None:
        html = "".join(pending).strip()
        pending.clear()
        if not is_blank(html):
            out.append(blocks.paragraph(html))

    for child in list(root.children):
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            pending.append(clean_inline(child, rw))
            continue
        name = child.name
        if name in DROP:
            continue
        if name == "form":
            rw.warnings.append("modulo HTML rimosso (non migrabile)")
            continue
        if name == "img":
            flush()
            out.append(image_from(child, rw))
            continue
        if name == "a" and child.find("img") is not None and not child.get_text(strip=True):
            flush()
            out.append(image_from(child.find("img"), rw, link=child.get("href")))
            continue
        if name in INLINE:
            pending.append(clean_inline(child, rw))
            continue
        flush()
        if name == "p":
            imgs = child.find_all("img")
            if imgs and not child.get_text(strip=True):
                out.extend(image_from(i, rw) for i in imgs)
            else:
                html = clean_inline(child, rw).strip()
                if not is_blank(html):
                    out.append(blocks.paragraph(html))
        elif re.fullmatch(r"h[1-6]", name):
            html = clean_inline(child, rw).strip()
            if not is_blank(html):
                out.append(blocks.heading(int(name[1]), html))
        elif name in ("ul", "ol"):
            out.append(list_from(child, rw))
        elif name == "figure":
            img = child.find("img")
            cap = child.find("figcaption")
            if img is not None:
                link = img.find_parent("a")
                out.append(
                    image_from(img, rw, link.get("href") if link else None,
                               clean_inline(cap, rw) if cap else "")
                )
            elif child.find("iframe") is not None:
                out.append(iframe_block(child.find("iframe"), rw))
        elif name == "iframe":
            out.append(iframe_block(child, rw))
        elif name == "hr":
            out.append(blocks.separator())
        elif name == "blockquote":
            inner = "".join(fragment_to_blocks(child, rw))
            out.append(blocks.wrap("quote", f'<blockquote class="wp-block-quote">{inner}</blockquote>'))
        elif name == "table":
            for tag in child.find_all(True):
                if tag.name not in TABLE_TAGS:
                    tag.unwrap() if tag.name in INLINE else tag.decompose()
            for tag in child.find_all(True):
                tag.attrs = {k: v for k, v in tag.attrs.items() if k in ("colspan", "rowspan")}
            out.append(blocks.wrap("table", f'<figure class="wp-block-table">{child}</figure>'))
        else:
            out.extend(fragment_to_blocks(child, rw))  # div, section, ecc.: scendo
    flush()
    return [b for b in out if b]


def html_to_blocks(html: str, rw: Rewriter) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    return fragment_to_blocks(soup, rw)

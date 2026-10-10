"""Serializzatori di blocchi Gutenberg core (markup compatibile con l'editor WP 6.x/7.x)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape


def serialize_attrs(attrs: dict) -> str:
    """JSON degli attributi come serializeAttributes() di WordPress: niente '--', '<', '>', '&', '"'
    letterali dentro il commento del blocco."""
    raw = json.dumps(attrs, ensure_ascii=False)
    raw = raw.replace("--", "\\u002d\\u002d").replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return re.sub(r'\\"', r"\\u0022", raw)


def _comment(name: str, attrs: dict | None) -> str:
    return f"<!-- wp:{name} {serialize_attrs(attrs)} -->" if attrs else f"<!-- wp:{name} -->"


def wrap(name: str, html: str, attrs: dict | None = None) -> str:
    return f"{_comment(name, attrs)}\n{html}\n<!-- /wp:{name} -->"


def paragraph(inner_html: str, align: str | None = None) -> str:
    if align:
        return wrap("paragraph", f'<p class="has-text-align-{align}">{inner_html}</p>', {"align": align})
    return wrap("paragraph", f"<p>{inner_html}</p>")


def heading(level: int, inner_html: str) -> str:
    level = min(max(level, 2), 6)
    attrs = None if level == 2 else {"level": level}
    return wrap("heading", f'<h{level} class="wp-block-heading">{inner_html}</h{level}>', attrs)


def list_block(items: list[str], ordered: bool = False) -> str:
    """items: HTML interno di ciascun <li> (può contenere liste annidate già serializzate)."""
    tag = "ol" if ordered else "ul"
    lis = "".join(wrap("list-item", f"<li>{item}</li>") for item in items)
    return wrap("list", f'<{tag} class="wp-block-list">{lis}</{tag}>', {"ordered": True} if ordered else None)


def image(
    url: str,
    media_id: int | None = None,
    alt: str = "",
    width: int | None = None,
    link: str | None = None,
    caption: str = "",
    align: str | None = None,
) -> str:
    attrs: dict = {}
    if media_id:
        attrs["id"] = media_id
    if width:
        attrs["width"] = f"{width}px"
    attrs["sizeSlug"] = "full" if width else "large"
    attrs["linkDestination"] = "custom" if link else "none"
    if align:
        attrs["align"] = align
    classes = ["wp-block-image", f"size-{attrs['sizeSlug']}"]
    if width:
        classes.append("is-resized")
    if align:
        classes.insert(1, f"align{align}")
    img_attrs = f'src="{escape(url)}" alt="{escape(alt)}"'
    if media_id:
        img_attrs += f' class="wp-image-{media_id}"'
    if width:
        img_attrs += f' style="width:{width}px"'
    img = f"<img {img_attrs}/>"
    if link:
        img = f'<a href="{escape(link)}">{img}</a>'
    cap = f'<figcaption class="wp-element-caption">{caption}</figcaption>' if caption else ""
    return wrap("image", f'<figure class="{" ".join(classes)}">{img}{cap}</figure>', attrs)


@dataclass(frozen=True)
class Button:
    text: str
    url: str
    new_tab: bool = False


def buttons(items: list[Button], outline: bool = False, justify: str | None = None) -> str:
    inner = []
    for b in items:
        attrs: dict = {}
        if b.new_tab:
            attrs.update({"linkTarget": "_blank", "rel": "noreferrer noopener"})
        if outline:
            attrs["className"] = "is-style-outline"
        target = ' target="_blank" rel="noreferrer noopener"' if b.new_tab else ""
        cls = "wp-block-button is-style-outline" if outline else "wp-block-button"
        html = (
            f'<div class="{cls}"><a class="wp-block-button__link wp-element-button" '
            f'href="{escape(b.url)}"{target}>{escape(b.text)}</a></div>'
        )
        inner.append(wrap("button", html, attrs or None))
    attrs = {"layout": {"type": "flex", "justifyContent": justify}} if justify else None
    cls = f"wp-block-buttons is-content-justification-{justify}" if justify else "wp-block-buttons"
    return wrap("buttons", f'<div class="{cls}">{"".join(inner)}</div>', attrs)


def spacer(height: int = 24) -> str:
    return wrap("spacer", f'<div style="height:{height}px" aria-hidden="true" class="wp-block-spacer"></div>',
                {"height": f"{height}px"})


def separator() -> str:
    return wrap("separator", '<hr class="wp-block-separator has-alpha-channel-opacity"/>')


def html_block(raw: str) -> str:
    return wrap("html", raw)


def youtube(url: str) -> str:
    attrs = {
        "url": url,
        "type": "video",
        "providerNameSlug": "youtube",
        "responsive": True,
        "className": "wp-embed-aspect-16-9 wp-has-aspect-ratio",
    }
    html = (
        '<figure class="wp-block-embed is-type-video is-provider-youtube wp-block-embed-youtube '
        'wp-embed-aspect-16-9 wp-has-aspect-ratio"><div class="wp-block-embed__wrapper">\n'
        f"{escape(url)}\n</div></figure>"
    )
    return wrap("embed", html, attrs)


def columns(cols: list[str]) -> str:
    inner = "".join(wrap("column", f'<div class="wp-block-column">{c}</div>') for c in cols)
    return wrap("columns", f'<div class="wp-block-columns">{inner}</div>')


def group(inner: str, class_name: str | None = None) -> str:
    attrs: dict = {"layout": {"type": "constrained"}}
    cls = "wp-block-group"
    if class_name:
        attrs = {"className": class_name, **attrs}
        cls += f" {class_name}"
    return wrap("group", f'<div class="{cls}">{inner}</div>', attrs)


def cover(url: str, media_id: int | None, inner: str, min_height: int = 420, dim: int = 50) -> str:
    attrs: dict = {"url": url}
    if media_id:
        attrs["id"] = media_id
    attrs.update({"dimRatio": dim, "minHeight": min_height, "minHeightUnit": "px", "isDark": True})
    img_cls = "wp-block-cover__image-background" + (f" wp-image-{media_id}" if media_id else "")
    html = (
        f'<div class="wp-block-cover is-dark" style="min-height:{min_height}px">'
        f'<span aria-hidden="true" class="wp-block-cover__background has-background-dim"></span>'
        f'<img class="{img_cls}" alt="" src="{escape(url)}" data-object-fit="cover"/>'
        f'<div class="wp-block-cover__inner-container">{inner}</div></div>'
    )
    return wrap("cover", html, attrs)

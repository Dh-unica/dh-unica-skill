"""Barra di sezione del progetto: orientamento dentro il minisito migrato.

Il menu globale del portale mostra le sottovoci del progetto solo a tendina: una volta dentro una
pagina (es. «Equipe») il visitatore non vede più dove si trova. La barra di sezione risolve:

  Progetti › La ricchezza della Chiesa                       ← percorso (breadcrumb)
  Il Progetto | Equipe | Eventi | Pubblicazioni | Contatti   ← menu del progetto, voce corrente evidenziata

È un pattern sincronizzato (wp_block) che contiene un blocco core/navigation collegato a un menu
WordPress (wp_navigation): si modifica in un solo punto e ogni pagina del progetto lo include con
<!-- wp:block {"ref": ID} /-->. La voce corrente è marcata da WordPress (classe current-menu-item).
"""
from __future__ import annotations

import json
import logging
from html import escape

from . import blocks
from .config import Config
from .wp_client import WPClient

log = logging.getLogger(__name__)

CSS = """<style>
.dh-progetto-nav{border-bottom:1px solid #d9dadb;padding:0 0 .5rem;margin:0 0 1.5rem}
.dh-progetto-nav .dh-progetto-percorso{font-size:.9rem;margin:0 0 .25rem}
.dh-progetto-nav .wp-block-navigation{gap:.25rem 1.5rem;font-weight:600}
.dh-progetto-nav .wp-block-navigation a{text-decoration:none;padding:.4rem 0;display:inline-block;border-bottom:3px solid transparent}
.dh-progetto-nav .wp-block-navigation a:hover{border-bottom-color:currentColor}
.dh-progetto-nav .current-menu-item>a{border-bottom-color:currentColor}
</style>"""


def navigation_content(cfg: Config, page_ids: dict[str, int]) -> str:
    """Contenuto del menu wp_navigation: le pagine con menu_label (radice esclusa)."""
    links = []
    for page in cfg.pages:
        if page.menu_label and page.parent is not None:
            attrs = {"label": page.menu_label, "type": "page", "id": page_ids[page.source_slug],
                     "url": cfg.target_link(page.source_slug), "kind": "post-type"}
            links.append(f"<!-- wp:navigation-link {blocks.serialize_attrs(attrs)} /-->")
    return "\n".join(links)


def pattern_content(cfg: Config, navigation_id: int) -> str:
    nav_cfg = cfg.section_nav
    trail = [f'<a href="{escape(c["url"])}">{escape(c["label"])}</a>' for c in nav_cfg.breadcrumb]
    root_label = (cfg.menu.label if cfg.menu and cfg.menu.label else None) or cfg.root.title or cfg.project_slug
    trail.append(f'<a href="{escape(cfg.target_link(cfg.root.source_slug))}"><strong>{escape(root_label)}</strong></a>')
    percorso = blocks.wrap(
        "paragraph", f'<p class="dh-progetto-percorso">{" › ".join(trail)}</p>', {"className": "dh-progetto-percorso"}
    )
    nav_attrs = {"ref": navigation_id, "overlayMenu": "never", "ariaLabel": f"Menu del progetto {root_label}",
                 "layout": {"type": "flex", "flexWrap": "wrap"}}
    navigation = f"<!-- wp:navigation {blocks.serialize_attrs(nav_attrs)} /-->"
    inner = "\n\n".join([blocks.html_block(CSS), percorso, navigation])
    return blocks.group(inner, "dh-progetto-nav")


def pattern_ref(block_id: int) -> str:
    return f"<!-- wp:block {json.dumps({'ref': block_id})} /-->"


def sync_section_nav(cfg: Config, client: WPClient, state) -> dict:
    """Crea/aggiorna menu wp_navigation e pattern sincronizzato (idempotente). Richiede le pagine create."""
    if cfg.section_nav is None:
        return {"section_nav": "disattivata"}
    page_ids = {slug: entry["id"] for slug, entry in state.pages.items()}
    label = (cfg.menu.label if cfg.menu and cfg.menu.label else None) or cfg.root.title or cfg.project_slug
    own = state.section_nav
    nav_data = {"title": f"Menu progetto: {label}", "content": navigation_content(cfg, page_ids), "status": "publish"}
    if own.get("navigation_id"):
        client.update_navigation(own["navigation_id"], nav_data)
    else:
        own["navigation_id"] = client.create_navigation(nav_data)["id"]
        state.save()
    block_data = {"title": f"Barra progetto: {label}", "content": pattern_content(cfg, own["navigation_id"]),
                  "status": "publish"}
    if own.get("block_id"):
        client.update_block(own["block_id"], block_data)
    else:
        own["block_id"] = client.create_block(block_data)["id"]
        state.save()
    log.info("barra di sezione: menu %s, pattern %s", own["navigation_id"], own["block_id"])
    return {"navigation_id": own["navigation_id"], "block_id": own["block_id"]}


def remove_section_nav(client: WPClient, state) -> dict:
    own = state.section_nav
    removed = {}
    if own.get("block_id"):
        client.delete_block(own.pop("block_id"))
        removed["block"] = True
    if own.get("navigation_id"):
        client.delete_navigation(own.pop("navigation_id"))
        removed["navigation"] = True
    state.save()
    return {"section_nav_removed": removed}

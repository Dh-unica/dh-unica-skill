"""Voci del progetto nel menu globale del portale.

Struttura: <menu.parent> (es. «Progetti») > <menu.label> (radice del progetto) > pagine con menu_label.
Le voci vengono inserite subito dopo l'ultimo discendente della voce genitore; le voci successive
vengono spostate in avanti e il loro ordine originale viene salvato nello stato per il rollback.
"""
from __future__ import annotations

import html as htmllib
import logging

from .config import Config
from .wp_client import WPClient, WPError

log = logging.getLogger(__name__)


def _title(item: dict) -> str:
    title = item.get("title", {})
    raw = title.get("raw") if isinstance(title, dict) else title
    return htmllib.unescape(raw or (title.get("rendered", "") if isinstance(title, dict) else "")).strip()


def resolve_menu_id(client: WPClient, location: str) -> int:
    locations = client.menu_locations()
    menu_id = (locations.get(location) or {}).get("menu", 0)
    if not menu_id:
        raise WPError(f"nessun menu assegnato alla location '{location}' (disponibili: {sorted(locations)})")
    return menu_id


def descendants(items: list[dict], root_id: int) -> list[dict]:
    children = [i for i in items if i["parent"] == root_id]
    out = list(children)
    for child in children:
        out.extend(descendants(items, child["id"]))
    return out


def render_tree(items: list[dict], parent: int = 0, depth: int = 0) -> list[str]:
    """Albero leggibile del menu (per survey e per chiedere conferma della posizione)."""
    lines = []
    for item in sorted((i for i in items if i["parent"] == parent), key=lambda i: i["menu_order"]):
        lines.append(f"{'  ' * depth}- {_title(item)}")
        lines.extend(render_tree(items, item["id"], depth + 1))
    return lines


def planned_entries(cfg: Config, page_ids: dict[str, int]) -> list[dict]:
    """Voci da creare, nell'ordine: prima la radice, poi le sottovoci."""
    label = cfg.menu.label or cfg.root.title or cfg.project_slug
    entries = [{"key": cfg.root.source_slug, "title": label, "object_id": page_ids[cfg.root.source_slug], "child": False}]
    for page in cfg.pages:
        if page.menu_label and page.parent is not None:
            entries.append({"key": page.source_slug, "title": page.menu_label,
                            "object_id": page_ids[page.source_slug], "child": True})
    return entries


def sync_menu(cfg: Config, client: WPClient, state) -> dict:
    """Crea o aggiorna le voci del progetto nel menu globale (idempotente)."""
    if cfg.menu is None:
        return {"menu": "non gestito (config senza sezione menu)"}
    menu_id = resolve_menu_id(client, cfg.menu.location)
    items = client.menu_items(menu_id)
    by_id = {i["id"]: i for i in items}
    parent_id = 0
    if cfg.menu.parent:
        matches = [i for i in items if _title(i).lower() == cfg.menu.parent.lower()]
        if len(matches) != 1:
            raise WPError(f"voce genitore '{cfg.menu.parent}' trovata {len(matches)} volte nel menu {menu_id}")
        parent_id = matches[0]["id"]

    page_ids = {slug: entry["id"] for slug, entry in state.pages.items()}
    entries = planned_entries(cfg, page_ids)
    own = state.menu.setdefault("items", {})
    stale = [key for key, item_id in own.items() if item_id not in by_id]
    for key in stale:  # voce cancellata a mano dal pannello: la ricreiamo
        del own[key]

    missing = [e for e in entries if e["key"] not in own]
    if missing:
        own_ids = set(own.values())
        anchor_tree = [i for i in descendants(items, parent_id) if i["id"] not in own_ids] if parent_id else []
        after = max([by_id[parent_id]["menu_order"]] + [i["menu_order"] for i in anchor_tree]) if parent_id else \
            max([i["menu_order"] for i in items] or [0])
        start = after + 1 + len(own)
        shifted = state.menu.setdefault("shifted", {})
        for item in items:
            if item["menu_order"] >= start and item["id"] not in own_ids:
                shifted.setdefault(str(item["id"]), item["menu_order"])
                client.update_menu_item(item["id"], {"menu_order": item["menu_order"] + len(missing)})
        state.menu["menu_id"] = menu_id
        state.save()
    else:
        start = None

    report = []
    order = start
    for entry in entries:
        parent = parent_id if not entry["child"] else own[cfg.root.source_slug]
        data = {"title": entry["title"], "type": "post_type", "object": "page", "object_id": entry["object_id"],
                "parent": parent, "menus": menu_id, "status": "publish"}
        if entry["key"] in own:
            client.update_menu_item(own[entry["key"]], data)
            action = "aggiornata"
        else:
            created = client.create_menu_item({**data, "menu_order": order})
            own[entry["key"]] = created["id"]
            order += 1
            state.save()
            action = "creata"
        report.append({"voce": entry["title"], "id": own[entry["key"]], "azione": action})
        log.info("voce di menu %s: %s (id %s)", action, entry["title"], own[entry["key"]])
    return {"menu_id": menu_id, "parent": cfg.menu.parent, "items": report}


def remove_menu(client: WPClient, state) -> dict:
    """Rollback: elimina le nostre voci (figlie prima) e ripristina l'ordine delle voci spostate."""
    own = state.menu.get("items", {})
    deleted = []
    for key in list(reversed(list(own))):
        client.delete_menu_item(own[key])
        deleted.append(own.pop(key))
        state.save()
    restored = []
    for item_id, order in list(state.menu.get("shifted", {}).items()):
        client.update_menu_item(int(item_id), {"menu_order": order})
        restored.append(int(item_id))
        del state.menu["shifted"][item_id]
        state.save()
    return {"menu_items_deleted": deleted, "menu_items_restored": restored}

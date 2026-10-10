#!/usr/bin/env python3
"""DH Unica slides renderer.

Usage:
    python render.py deck.yaml [output.html]
    python render.py deck.yaml --marp [output.md]

Genera presentazioni nello stile grafico DH Unica (dh.unica.it).
Schema del deck: vedi schema/deck.schema.json e examples/example-deck.yaml.
"""
from __future__ import annotations

import json
import shutil
import sys
from html import escape
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SKILL_DIR / "assets"
TEMPLATES_DIR = SKILL_DIR / "templates"

# rotazione colori accento (icone home dh.unica.it)
ACCENTS = [
    "var(--dh-acc-red)", "var(--dh-acc-blue)", "var(--dh-acc-green)",
    "var(--dh-acc-magenta)", "var(--dh-acc-teal)", "var(--dh-acc-orange)",
]


def load_deck(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError:
            sys.exit("PyYAML richiesto per input YAML: pip install pyyaml")
        return yaml.safe_load(text)
    return json.loads(text)


# ---------- decori comuni ----------

def _chrome(footer: bool = True) -> str:
    head = (
        '<div class="bg-glow"></div>'
        '<div class="slide-header"><img class="dh-logo" src="assets/dh-logo-black.png" alt="DH Unica"></div>'
        '<div class="bg-strip"></div>'
    )
    if footer:
        head += '<div class="slide-footer"></div>'
    return head


# ---------- HTML LAYOUT RENDERERS ----------

def render_cover(s: dict) -> str:
    subtitle = s.get("subtitle", "")
    contacts_html = ""
    for c in s.get("contacts", []) or []:
        if isinstance(c, dict):
            name = escape(c.get("name", ""))
            role = c.get("role", "")
            role_html = f' <span class="role">— {escape(role)}</span>' if role else ""
            contacts_html += f"<div>{name}{role_html}</div>"
        else:
            contacts_html += f"<div>{escape(c)}</div>"
    return f'''<section class="slide layout-cover">
  <div class="bg-glow"></div>
  <div class="bg-strip"></div>
  <div class="cover-inner">
    <h1>{escape(s.get("title", ""))}</h1>
    {f'<div class="subtitle">{escape(subtitle)}</div>' if subtitle else ''}
    {f'<div class="contacts">{contacts_html}</div>' if contacts_html else ''}
  </div>
  <img class="cover-logo" src="assets/dh-logo-black.png" alt="DH Unica">
</section>'''


def render_divider(s: dict) -> str:
    subtitle = s.get("subtitle", "")
    return f'''<section class="slide layout-divider">
  <div class="bg-glow"></div>
  <div class="bg-strip"></div>
  <div class="slide-header"><img class="dh-logo" src="assets/dh-logo-black.png" alt="DH Unica"></div>
  <div class="divider-inner">
    <h1>{escape(s.get("title", ""))}</h1>
    {f'<div class="subtitle">{escape(subtitle)}</div>' if subtitle else ''}
  </div>
</section>'''


def render_lead_bullets(s: dict) -> str:
    lead = s.get("lead", "")
    bullets = "".join(f"<li>{escape(b)}</li>" for b in s.get("bullets", []) or [])
    img = s.get("image", "")
    has_img = bool(img) or bool(s.get("image_box"))
    img_html = (
        f'<img src="{escape(img)}" alt="">' if img else "[immagine]"
    )
    image_col = f'<div class="lb-image">{img_html}</div>' if has_img else ""
    grid_cls = "lb-grid" if has_img else "lb-grid no-image"
    left = (
        (f'<p class="dh-lead">{escape(lead)}</p>' if lead else '')
        + (f'<div class="lb-panel"><ul>{bullets}</ul></div>' if bullets else '')
    )
    return f'''<section class="slide layout-lead">
  {_chrome()}
  <div class="slide-body">
    <h1 class="dh-title">{escape(s.get("title", ""))}</h1>
    <div class="{grid_cls}">
      <div>{left}</div>
      {image_col}
    </div>
  </div>
</section>'''


def render_cards(s: dict) -> str:
    cards = s.get("cards", [])
    n = len(cards)
    cols = s.get("columns") or (3 if n % 3 == 0 or n >= 5 else (n if n in (1, 2) else 3))
    lead = s.get("lead", "")
    parts = []
    for i, c in enumerate(cards):
        accent = c.get("color") or ACCENTS[i % len(ACCENTS)]
        icon = c.get("icon", "")
        kicker = c.get("kicker", "")
        icon_html = f'<div class="card-icon">{escape(icon)}</div>' if icon else ""
        kicker_html = f'<div class="card-kicker">{escape(kicker)}</div>' if kicker else ""
        parts.append(
            f'<div class="dh-card" style="--dh-card-accent:{accent}">'
            f'{icon_html}{kicker_html}'
            f'<h3>{escape(c.get("heading", ""))}</h3>'
            f'<p>{escape(c.get("body", ""))}</p>'
            f'</div>'
        )
    cards_html = "\n".join(parts)
    return f'''<section class="slide layout-cards">
  {_chrome()}
  <div class="slide-body">
    <h1 class="dh-title">{escape(s.get("title", ""))}</h1>
    {f'<p class="dh-lead">{escape(lead)}</p>' if lead else ''}
    <div class="cards-grid cols-{cols}">
      {cards_html}
    </div>
  </div>
</section>'''


def render_tech_list(s: dict) -> str:
    lead = s.get("lead", "")
    img = s.get("image", "")
    has_img = bool(img) or bool(s.get("image_box"))
    items = []
    for it in s.get("items", []) or []:
        badge = it.get("badge", "")
        badge_html = f'<span class="badge">{escape(badge)}</span>' if badge else ""
        items.append(
            f'<div class="tl-item">{badge_html}'
            f'<h3>{escape(it.get("name", ""))}</h3>'
            f'<p>{escape(it.get("body", ""))}</p></div>'
        )
    items_html = "\n".join(items)
    img_html = f'<img src="{escape(img)}" alt="">' if img else "[immagine / diagramma]"
    image_col = f'<div class="tl-image">{img_html}</div>' if has_img else ""
    grid_cls = "tl-grid" if has_img else "tl-grid no-image"
    return f'''<section class="slide layout-tech">
  {_chrome()}
  <div class="slide-body">
    <h1 class="dh-title">{escape(s.get("title", ""))}</h1>
    {f'<p class="dh-lead">{escape(lead)}</p>' if lead else ''}
    <div class="{grid_cls}">
      <div class="tl-list">{items_html}</div>
      {image_col}
    </div>
  </div>
</section>'''


def render_table(s: dict) -> str:
    headers = s.get("headers", [])
    rows = s.get("rows", [])
    thead = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    tbody = ""
    for row in rows:
        tds = "".join(f"<td>{escape(str(c))}</td>" for c in row)
        tbody += f"<tr>{tds}</tr>"
    lead = s.get("lead", "")
    return f'''<section class="slide layout-table">
  {_chrome()}
  <div class="slide-body">
    <h1 class="dh-title">{escape(s.get("title", ""))}</h1>
    {f'<p class="dh-lead">{escape(lead)}</p>' if lead else ''}
    <table class="dh-table">
      <thead><tr>{thead}</tr></thead>
      <tbody>{tbody}</tbody>
    </table>
  </div>
</section>'''


def render_stats(s: dict) -> str:
    stats = s.get("stats", [])
    cols = s.get("columns") or len(stats) or 3

    def _stat(st: dict) -> str:
        hint = st.get("hint", "")
        hint_html = f'<div class="hint">{escape(hint)}</div>' if hint else ""
        return (
            f'<div class="stat-item">'
            f'<div class="value">{escape(str(st.get("value", "")))}</div>'
            f'<div class="label">{escape(st.get("label", ""))}</div>'
            f'{hint_html}</div>'
        )

    items = "\n".join(_stat(st) for st in stats)
    desc = s.get("description", "")
    return f'''<section class="slide layout-stats">
  {_chrome()}
  <div class="slide-body">
    <h1 class="dh-title">{escape(s.get("title", ""))}</h1>
    <div class="stats-row cols-{cols}">
      {items}
    </div>
    {f'<div class="stats-desc">{escape(desc)}</div>' if desc else ''}
  </div>
</section>'''


def render_showcase(s: dict) -> str:
    img = s.get("image", "")
    inner = (
        f'<img src="{escape(img)}" alt="">' if img
        else '<div class="placeholder">[inserisci immagine / screenshot]</div>'
    )
    return f'''<section class="slide layout-showcase">
  {_chrome()}
  <div class="slide-body">
    <h1 class="dh-title">{escape(s.get("title", ""))}</h1>
    <div class="showcase"><div class="frame">{inner}</div></div>
  </div>
</section>'''


def render_closing(s: dict) -> str:
    subtitle = s.get("subtitle", "")
    credits_html = ""
    for c in s.get("credits", []) or []:
        if isinstance(c, dict) and c.get("site"):
            credits_html += f'<div class="site">{escape(c["site"])}</div>'
        else:
            credits_html += f"<div>{escape(c if isinstance(c, str) else c.get('text',''))}</div>"
    title = s.get("title", "Domande?")
    return f'''<section class="slide layout-closing">
  <div class="bg-glow"></div>
  <div class="bg-strip"></div>
  <div class="closing-inner">
    <h1>{escape(title)}</h1>
    {f'<div class="subtitle">{escape(subtitle)}</div>' if subtitle else ''}
    {f'<div class="credits">{credits_html}</div>' if credits_html else ''}
  </div>
  <img class="closing-logo" src="assets/dh-logo-white.png" alt="DH Unica">
</section>'''


LAYOUTS = {
    "cover": render_cover,
    "section-divider": render_divider,
    "lead-bullets": render_lead_bullets,
    "cards": render_cards,
    "tech-list": render_tech_list,
    "table": render_table,
    "stats-row": render_stats,
    "image-showcase": render_showcase,
    "closing": render_closing,
}


# ---------- HTML COMPOSER ----------

def render_html(deck: dict, out_path: Path) -> Path:
    slides_html = []
    for s in deck.get("slides", []):
        layout = s.get("layout")
        fn = LAYOUTS.get(layout)
        if not fn:
            raise ValueError(f"Layout sconosciuto: {layout!r}. Disponibili: {list(LAYOUTS)}")
        slides_html.append(fn(s))

    theme = deck.get("theme", {}) or {}
    theme_map = {
        "navy": "--dh-navy", "blue": "--dh-blue",
        "blue_mid": "--dh-blue-mid", "cyan": "--dh-cyan",
    }
    overrides = [f"{var}: {theme[k]};" for k, var in theme_map.items() if k in theme]
    overrides_css = (":root{" + " ".join(overrides) + "}") if overrides else ""

    base = (TEMPLATES_DIR / "html" / "base.html").read_text(encoding="utf-8")
    html = (
        base.replace("{{TITLE}}", escape(deck.get("title", "DH Unica")))
            .replace("{{SLIDES}}", "\n".join(slides_html))
            .replace("{{THEME_OVERRIDES}}", overrides_css)
    )

    out_path = out_path.resolve()
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_assets = out_dir / "assets"
    out_assets.mkdir(exist_ok=True)

    shutil.copy(TEMPLATES_DIR / "html" / "styles.css", out_assets / "styles.css")
    for name in ("dh-logo-black.png", "dh-logo-white.png", "dh-mark-black.svg", "dh-mark-white.svg"):
        src = ASSETS_DIR / name
        if src.exists():
            shutil.copy(src, out_assets / name)

    out_path.write_text(html, encoding="utf-8")
    return out_path


# ---------- MARP RENDERER ----------

MARP_HEADER = """---
marp: true
theme: dh-unica
paginate: true
size: 16:9
---

"""


def render_marp(deck: dict, out_path: Path) -> Path:
    lines = [MARP_HEADER]
    for s in deck.get("slides", []):
        layout = s.get("layout")
        if layout == "cover":
            sub = s.get("subtitle", "")
            lines.append(f'<!-- _class: cover -->\n# {s.get("title","")}\n\n*{sub}*\n')
        elif layout == "section-divider":
            lines.append(f'<!-- _class: divider -->\n# {s.get("title","")}\n\n{s.get("subtitle","")}\n')
        elif layout == "lead-bullets":
            blk = f"# {s.get('title','')}\n\n**{s.get('lead','')}**\n\n"
            for b in s.get("bullets", []) or []:
                blk += f"- {b}\n"
            lines.append(blk)
        elif layout == "cards":
            blk = f"# {s.get('title','')}\n\n{s.get('lead','')}\n\n<div class='cards'>\n"
            for c in s.get("cards", []):
                blk += f"<div class='card'><h3>{c.get('heading','')}</h3><p>{c.get('body','')}</p></div>\n"
            blk += "</div>\n"
            lines.append(blk)
        elif layout == "tech-list":
            blk = f"# {s.get('title','')}\n\n{s.get('lead','')}\n\n"
            for it in s.get("items", []) or []:
                blk += f"**{it.get('name','')}** — {it.get('body','')}\n\n"
            lines.append(blk)
        elif layout == "table":
            blk = f"# {s.get('title','')}\n\n"
            headers = s.get("headers", [])
            if headers:
                blk += "| " + " | ".join(map(str, headers)) + " |\n"
                blk += "|" + "---|" * len(headers) + "\n"
                for row in s.get("rows", []):
                    blk += "| " + " | ".join(map(str, row)) + " |\n"
            lines.append(blk)
        elif layout == "stats-row":
            blk = f"# {s.get('title','')}\n\n<div class='stats'>\n"
            for st in s.get("stats", []):
                blk += f"<div><b>{st.get('value','')}</b><br>{st.get('label','')}</div>\n"
            blk += "</div>\n\n" + s.get("description", "") + "\n"
            lines.append(blk)
        elif layout == "image-showcase":
            img = s.get("image", "")
            blk = f"# {s.get('title','')}\n\n"
            blk += f"![]({img})\n" if img else "*(immagine)*\n"
            lines.append(blk)
        elif layout == "closing":
            lines.append(f"<!-- _class: closing -->\n# {s.get('title','Domande?')}\n\n{s.get('subtitle','')}\n")
        lines.append("\n---\n")

    text = "".join(lines)
    if text.endswith("\n---\n"):
        text = text[: -len("\n---\n")] + "\n"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    theme_src = TEMPLATES_DIR / "marp" / "theme.css"
    if theme_src.exists():
        shutil.copy(theme_src, out_path.parent / "dh-unica-theme.css")
    return out_path


# ---------- CLI ----------

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    input_path = Path(argv[1])
    marp = "--marp" in argv
    args = [a for a in argv[2:] if a != "--marp"]
    output = Path(args[0]) if args else None

    deck = load_deck(input_path)
    title = deck.get("title", "dh-unica-deck")
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in title)

    if marp or deck.get("output") == "marp":
        out = output or Path(f"{safe}.md")
        result = render_marp(deck, out)
    else:
        out = output or Path(f"{safe}.html")
        result = render_html(deck, out)

    print(f"✓ Generato: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

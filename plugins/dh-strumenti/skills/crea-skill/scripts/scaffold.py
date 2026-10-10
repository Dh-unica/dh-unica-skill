#!/usr/bin/env python3
"""Crea una nuova skill (ed eventualmente un nuovo plugin) nel marketplace dh-unica-skill dai modelli.

Uso:
  python3 scaffold.py --root <marketplace> --plugin dh-<area> --skill <azione-oggetto> \\
      --skill-descrizione "..." --livello "sola lettura|bozze|produzione" \\
      [--plugin-descrizione "..."] [--manutentore "Nome Cognome"] [--categoria siti-web]

Se il plugin esiste già, aggiunge solo la cartella della skill e una riga nella tabella del README.
Non sovrascrive mai file esistenti.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template"
PLUGIN_RE = re.compile(r"^dh-[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LIVELLI = ("sola lettura", "bozze", "produzione")


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def copy_template(src: Path, dst: Path, values: dict[str, str]) -> list[Path]:
    created = []
    for path in sorted(src.rglob("*")):
        if path.is_dir():
            continue
        target = dst / path.relative_to(src)
        if target.exists():
            continue  # mai sovrascrivere
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(path.read_text(encoding="utf-8"), values), encoding="utf-8")
        created.append(target)
    return created


def register_plugin(root: Path, plugin: str, description: str, category: str) -> bool:
    path = root / ".claude-plugin" / "marketplace.json"
    market = json.loads(path.read_text(encoding="utf-8"))
    if any(p["name"] == plugin for p in market["plugins"]):
        return False
    market["plugins"].append({"name": plugin, "source": f"./plugins/{plugin}", "description": description,
                              "category": category, "tags": ["dh-unica"]})
    market["plugins"].sort(key=lambda p: p["name"])
    path.write_text(json.dumps(market, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def add_index_row(root: Path, plugin: str, skill: str, description: str, livello: str) -> None:
    """Aggiunge la riga della skill alla tabella «Catalogo» del README del marketplace."""
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    row = f"| `{plugin}` | `/{plugin}:{skill}` | {description} | {livello} |"
    if f"`/{plugin}:{skill}`" in text:
        return
    marker = "<!-- fine-catalogo -->"
    if marker not in text:
        raise SystemExit(f"{readme}: manca il segnaposto {marker} sotto la tabella del catalogo")
    readme.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def add_skill_row_to_plugin_readme(plugin_dir: Path, plugin: str, skill: str, livello: str) -> None:
    readme = plugin_dir / "README.md"
    text = readme.read_text(encoding="utf-8")
    if f"`/{plugin}:{skill}`" in text:
        return
    lines = text.splitlines()
    last_row = max(i for i, line in enumerate(lines) if line.startswith("| `"))
    lines.insert(last_row + 1, f"| `{skill}` | `/{plugin}:{skill}` | {livello} |")
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="radice del marketplace")
    ap.add_argument("--plugin", required=True)
    ap.add_argument("--skill", required=True)
    ap.add_argument("--skill-descrizione", required=True)
    ap.add_argument("--livello", required=True, choices=LIVELLI)
    ap.add_argument("--plugin-descrizione", default="")
    ap.add_argument("--manutentore", default="Centro DH UNICA")
    ap.add_argument("--categoria", default="dh-unica")
    args = ap.parse_args(argv)

    if not PLUGIN_RE.match(args.plugin):
        ap.error("--plugin deve essere dh-<area> in minuscolo con trattini (es. dh-archivi)")
    if not SKILL_RE.match(args.skill) or args.skill.startswith("dh-") or args.skill.endswith("-dh"):
        ap.error("--skill deve essere <azione>-<oggetto> in kebab-case, senza 'dh' (es. pubblicazione-dataset)")

    root = Path(args.root).resolve()
    plugin_dir = root / "plugins" / args.plugin
    skill_dir = plugin_dir / "skills" / args.skill
    if skill_dir.exists():
        print(f"La skill esiste già: {skill_dir}", file=sys.stderr)
        return 1
    new_plugin = not plugin_dir.exists()
    if new_plugin and not args.plugin_descrizione:
        ap.error("plugin nuovo: serve --plugin-descrizione")
    values = {
        "plugin": args.plugin, "skill": args.skill, "skill_descrizione": args.skill_descrizione,
        "plugin_descrizione": args.plugin_descrizione, "livello": args.livello,
        "manutentore": args.manutentore, "data": dt.date.today().isoformat(),
    }
    created = []
    if new_plugin:
        created += copy_template(TEMPLATE / "plugin", plugin_dir, values)
        register_plugin(root, args.plugin, args.plugin_descrizione, args.categoria)
    else:
        add_skill_row_to_plugin_readme(plugin_dir, args.plugin, args.skill, args.livello)
    created += copy_template(TEMPLATE / "skill", skill_dir, values)
    add_index_row(root, args.plugin, args.skill, args.skill_descrizione.split(".")[0], args.livello)
    for path in created:
        print(f"creato  {path.relative_to(root)}")
    print("\nProssimi passi: completa i TODO, aggiorna CHANGELOG e version, poi esegui check_skills.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Mappa dei redirect 301 dal vecchio dominio alle nuove URL DH.

Il vecchio dominio non è gestito dal DH: produciamo gli artefatti pronti da applicare
sull'hosting sorgente (CSV, regole Apache .htaccess, blocco nginx).
"""
from __future__ import annotations

import csv
import io
import json
from urllib.parse import urlparse

from .config import Config


def redirect_map(cfg: Config) -> list[tuple[str, str]]:
    pages = json.loads((cfg.project_dir / "extract" / "pages.json").read_text(encoding="utf-8"))
    configured = {p.source_slug for p in cfg.pages}
    pairs = [(urlparse(p["link"]).path or "/", cfg.target_link(p["slug"])) for p in pages if p["slug"] in configured]
    return sorted(pairs, key=lambda pair: (pair[0] != "/", pair[0]))


def to_csv(pairs: list[tuple[str, str]], source_url: str) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["old_url", "new_url", "status"])
    writer.writerows((source_url.rstrip("/") + old, new, 301) for old, new in pairs)
    return buf.getvalue()


def to_htaccess(pairs: list[tuple[str, str]], new_root: str) -> str:
    lines = ["# Redirect 301 verso il portale DH UniCA", "RewriteEngine On"]
    for old, new in pairs:
        pattern = "^$" if old == "/" else f"^{old.strip('/')}/?$"
        lines.append(f"RewriteRule {pattern} {new} [R=301,L]")
    lines.append(f"RewriteRule ^(.*)$ {new_root} [R=301,L]")
    return "\n".join(lines) + "\n"


def to_nginx(pairs: list[tuple[str, str]], new_root: str) -> str:
    lines = ["# Redirect 301 verso il portale DH UniCA (dentro il blocco server del vecchio dominio)"]
    for old, new in pairs:
        if old == "/":
            lines.append(f"location = / {{ return 301 {new}; }}")
        else:
            lines.append(f"location ~ ^{old.rstrip('/')}/?$ {{ return 301 {new}; }}")
    lines.append(f"location / {{ return 301 {new_root}; }}")
    return "\n".join(lines) + "\n"


def write_redirects(cfg: Config, out_dir) -> list[str]:
    pairs = redirect_map(cfg)
    root = cfg.target_link(cfg.root.source_slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        f"redirect-map-{cfg.project_slug}.csv": to_csv(pairs, cfg.source_url),
        f"redirect-{cfg.project_slug}.htaccess": to_htaccess(pairs, root),
        f"redirect-{cfg.project_slug}.nginx.conf": to_nginx(pairs, root),
    }
    for name, content in files.items():
        (out_dir / name).write_text(content, encoding="utf-8")
    return sorted(files)

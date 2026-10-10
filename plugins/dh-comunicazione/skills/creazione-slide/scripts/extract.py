#!/usr/bin/env python3
"""Estrae il contenuto testuale, le tabelle e le immagini da un .pptx o .pdf,
slide per slide, emettendo un JSON che Claude può poi mappare sul catalogo
layout DH Unica.

Usage:
    python extract.py input.pptx [out.json] [--media DIR]
    python extract.py input.pdf  [out.json]

--media DIR  estrae le immagini incorporate (solo .pptx) in DIR e aggiunge a
             ogni slide la lista `images` con i file collegati. Le immagini
             ricorrenti su quasi tutte le slide (loghi/decori) e quelle molto
             piccole (icone) sono marcate `decorative: true` così Claude sa
             distinguere il contenuto vero dai decori.

Nessuna dipendenza esterna: il .pptx viene letto come zip+XML, il .pdf via
`pdftotext` (poppler) se disponibile, con fallback a `pdfplumber`/`PyPDF2`.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

# soglia (in byte) sotto la quale un'immagine è considerata icona/decoro
DECOR_MIN_BYTES = 8000


def _slide_sort_key(name: str) -> int:
    m = re.search(r"slide(\d+)\.xml", name)
    return int(m.group(1)) if m else 0


def _slide_media(z: zipfile.ZipFile, slide_name: str) -> list[str]:
    """Restituisce i nomi file (ppt/media/...) collegati a una slide via .rels."""
    rels = slide_name.replace("slides/", "slides/_rels/") + ".rels"
    try:
        rroot = ET.fromstring(z.read(rels))
    except KeyError:
        return []
    R = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    out = []
    for rel in rroot.iter(f"{R}Relationship"):
        tgt = rel.get("Target", "")
        if "media/" in tgt:
            out.append("ppt/media/" + tgt.split("media/")[-1])
    return out


def extract_pptx(path: Path, media_dir: Path | None = None) -> list[dict]:
    slides = []
    with zipfile.ZipFile(path) as z:
        names = sorted(
            [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
            key=_slide_sort_key,
        )
        # conteggio occorrenze per individuare loghi/decori ricorrenti
        media_by_slide = {n: _slide_media(z, n) for n in names}
        freq: dict[str, int] = {}
        for lst in media_by_slide.values():
            for m in set(lst):
                freq[m] = freq.get(m, 0) + 1
        sizes = {m: z.getinfo(m).file_size for m in freq if m in z.namelist()}

        if media_dir:
            media_dir.mkdir(parents=True, exist_ok=True)
            for m in freq:
                if m in z.namelist():
                    (media_dir / Path(m).name).write_bytes(z.read(m))

        for i, name in enumerate(names, 1):
            root = ET.fromstring(z.read(name))
            texts: list[str] = []
            tables: list[list[list[str]]] = []
            images = []
            for m in media_by_slide.get(name, []):
                decorative = freq.get(m, 0) >= max(2, len(names) - 1) or sizes.get(m, 0) < DECOR_MIN_BYTES
                images.append({
                    "file": Path(m).name,
                    "bytes": sizes.get(m, 0),
                    "used_in_slides": freq.get(m, 0),
                    "decorative": decorative,
                })

            # tabelle (a:tbl): raccogli righe/celle
            for tbl in root.iter(f"{A}tbl"):
                rows = []
                for tr in tbl.iter(f"{A}tr"):
                    cells = []
                    for tc in tr.iter(f"{A}tc"):
                        cell_txt = "".join(t.text or "" for t in tc.iter(f"{A}t"))
                        cells.append(cell_txt.strip())
                    if cells:
                        rows.append(cells)
                if rows:
                    tables.append(rows)

            # paragrafi (a:p) NON dentro tabelle → testo libero (titoli, bullet, ecc.)
            in_table_t = {id(t) for tbl in root.iter(f"{A}tbl") for t in tbl.iter(f"{A}t")}
            for p in root.iter(f"{A}p"):
                runs = [t.text or "" for t in p.iter(f"{A}t") if id(t) not in in_table_t]
                line = "".join(runs).strip()
                if line:
                    texts.append(line)

            slides.append({"index": i, "texts": texts, "tables": tables, "images": images})
    return slides


def extract_pdf(path: Path) -> list[dict]:
    import shutil
    import subprocess

    if shutil.which("pdftotext"):
        out = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, text=True, check=True,
        ).stdout
        pages = out.split("\f")
        return [
            {"index": i, "texts": [l.strip() for l in pg.splitlines() if l.strip()], "tables": []}
            for i, pg in enumerate(pages, 1) if pg.strip()
        ]

    try:
        import pdfplumber  # type: ignore
        slides = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                txt = page.extract_text() or ""
                slides.append({
                    "index": i,
                    "texts": [l.strip() for l in txt.splitlines() if l.strip()],
                    "tables": page.extract_tables() or [],
                })
        return slides
    except ImportError:
        sys.exit("Per i PDF serve `pdftotext` (poppler-utils) oppure `pip install pdfplumber`.")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    rest = argv[2:]
    media_dir = None
    if "--media" in rest:
        mi = rest.index("--media")
        media_dir = Path(rest[mi + 1]) if mi + 1 < len(rest) else Path("media")
        rest = rest[:mi] + rest[mi + 2:]

    src = Path(argv[1])
    if not src.exists():
        sys.exit(f"File non trovato: {src}")

    if src.suffix.lower() == ".pptx":
        slides = extract_pptx(src, media_dir)
    elif src.suffix.lower() == ".pdf":
        if media_dir:
            print("Nota: --media è supportato solo per .pptx; per i PDF estrai gli screenshot con pdftoppm.", file=sys.stderr)
        slides = extract_pdf(src)
    else:
        sys.exit("Formato non supportato: usa .pptx o .pdf")

    data = {"source": src.name, "slide_count": len(slides), "slides": slides}
    out = Path(rest[0]) if rest else None
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if out:
        out.write_text(payload, encoding="utf-8")
        print(f"✓ Estratto {len(slides)} slide → {out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

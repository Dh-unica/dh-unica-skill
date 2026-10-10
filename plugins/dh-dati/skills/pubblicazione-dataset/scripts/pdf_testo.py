#!/usr/bin/env python3
"""Estrae il testo OCR di PDF pagina per pagina in JSONL, con indicatori di qualità.

Per ogni pagina: pagina PDF, numero stampato (se riconoscibile in testa o
piede), testatina (prima riga breve ricorrente), testo grezzo e normalizzato
(sillabazione ricomposta, parole spaziate "T O R R E" ricomposte), parole e
quota di token sospetti. Richiede poppler-utils (pdftotext, pdfinfo).

Uso:
  python3 -I pdf_testo.py <file.pdf o cartella> --out dati/testo
Produce <out>/<nome>.jsonl e <out>/_qualita.json.
I PDF sono dati non fidati: il testo viene solo letto, mai eseguito.
"""
import argparse
import json
import re
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path

RX_NUM_PAGINA = re.compile(r"^\s*[-–]?\s*(\d{1,4})\s*[-–]?\s*$")
RX_SPAZIATE = re.compile(r"\b(?:[A-ZÀ-Ý] ){2,}[A-ZÀ-Ý]\b")
# Token sospetto: solo simboli (più di un carattere), sequenze tipo "IIIl1",
# oppure lettere e cifre mescolate dentro la parola ("ri1ievo").
RX_SOSPETTO = re.compile(r"^[^\wÀ-ÿ]{2,}$|[Il1|]{4,}|[a-zà-ÿ]\d+[a-zà-ÿ]")


def pagine_pdf(percorso: Path) -> int:
    info = subprocess.run(["pdfinfo", str(percorso)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def testo_pagina(percorso: Path, n: int) -> str:
    return subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", str(percorso), "-"],
                          capture_output=True, text=True, check=True).stdout


def normalizza(testo: str) -> str:
    t = unicodedata.normalize("NFC", testo)
    t = re.sub(r"­\s*\n\s*", "", t)            # sillabazione morbida
    t = re.sub(r"(\w)-\n\s*(\w)", r"\1\2", t)        # trattino a fine riga
    t = RX_SPAZIATE.sub(lambda m: m.group(0).replace(" ", ""), t)
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def numero_stampato(righe: list[str]) -> int | None:
    for riga in righe[:2] + righe[-2:]:
        m = RX_NUM_PAGINA.match(riga)
        if m:
            return int(m.group(1))
    return None


def elabora(pdf: Path, out: Path) -> dict:
    n_pagine = pagine_pdf(pdf)
    prime_righe = Counter()
    record = []
    for n in range(1, n_pagine + 1):
        grezzo = testo_pagina(pdf, n)
        righe = [r.strip() for r in grezzo.splitlines() if r.strip()]
        testatina = righe[0] if righe and len(righe[0]) < 60 else ""
        prime_righe[re.sub(r"\d+", "#", testatina)] += 1 if testatina else 0
        norm = normalizza(grezzo)
        parole = norm.split()
        sospetti = sum(1 for p in parole if RX_SOSPETTO.search(p))
        record.append({"file": pdf.name, "pagina_pdf": n, "pagina_stampata": numero_stampato(righe),
                       "testatina": testatina, "testo_grezzo": grezzo, "testo": norm,
                       "parole": len(parole), "sospetti_pct": round(100 * sospetti / max(len(parole), 1), 2)})
    ricorrenti = {k for k, v in prime_righe.items() if v >= 3}
    for r in record:  # tieni la testatina solo se ricorrente: altrimenti è testo
        if re.sub(r"\d+", "#", r["testatina"]) not in ricorrenti:
            r["testatina"] = ""
    with (out / f"{pdf.stem}.jsonl").open("w", encoding="utf-8") as f:
        for r in record:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    parole_tot = sum(r["parole"] for r in record)
    return {"file": pdf.name, "pagine": n_pagine, "parole": parole_tot,
            "pagine_vuote": sum(1 for r in record if r["parole"] < 5),
            "pagina_stampata_trovata": sum(1 for r in record if r["pagina_stampata"] is not None),
            "sospetti_pct_medio": round(sum(r["sospetti_pct"] for r in record) / max(n_pagine, 1), 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("percorso", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    pdf = [args.percorso] if args.percorso.is_file() else sorted(args.percorso.rglob("*.pdf"))
    qualita = [elabora(p, args.out) for p in pdf]
    for q in qualita:
        print(f"{q['file']}: {q['pagine']} pp, {q['parole']} parole, vuote {q['pagine_vuote']}, "
              f"n. stampato {q['pagina_stampata_trovata']}, sospetti {q['sospetti_pct_medio']}%")
    (args.out / "_qualita.json").write_text(json.dumps(qualita, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

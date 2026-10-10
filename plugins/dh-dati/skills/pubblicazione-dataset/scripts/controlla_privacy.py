#!/usr/bin/env python3
"""Cerca dati personali sensibili in file di testo, JSON, JS, HTML, CSV, MD.

Segnala: telefoni, email, date di nascita complete, codici fiscali,
indirizzi ("via", "piazza", "c/o", "presso", "res."). È un allarme, non una
garanzia: rileggi a mano i risultati.

Uso:
  python3 -I controlla_privacy.py <cartella o file> [--max 20]
Esce con codice 1 se trova qualcosa (utile in un controllo prima del push).
"""
import argparse
import re
import sys
from pathlib import Path

ESTENSIONI = {".txt", ".json", ".js", ".html", ".htm", ".csv", ".md", ".tsv", ".xml"}
CONTROLLI = {
    # Solo numeri introdotti da "tel./cell./fax" o scritti con un separatore
    # (es. 070 123456): le cifre nude sono quasi sempre ID (OSM, Wikidata, record).
    "telefono": re.compile(r"\b(?i:tel|telefono|cell|cellulare|fax)\.?\s*:?\s*\+?\d[\d ./-]{5,14}\d"
                           r"|(?<![\w./-])(?:\+39[ .])?0\d{1,3}[ /.-]\d{4,8}(?![\w./-])"
                           r"|(?<![\w./-])3\d{2}[ .]\d{6,7}(?![\w./-])"),
    "email": re.compile(r"\b[\w.+-]+@(?:[\w-]+\.)+[A-Za-z]{2,}\b"),
    "data_nascita": re.compile(r"\b(nat[oa]|n\.)\s+(a\s+\S+\s+)?(il\s+)?\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", re.IGNORECASE),
    "codice_fiscale": re.compile(r"\b[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]\b"),
    # Il nome della via deve iniziare con una maiuscola ed essere seguito da un civico:
    # così "corso del 1965" o "presso il Tribunale" non vengono segnalati.
    "indirizzo": re.compile(r"\b(?i:via|viale|piazza|corso|vicolo|largo)\s+(?!(?i:del|della|dei|di)\b)"
                            r"[A-Z][\w'.]+(?:\s+[A-Z][\w'.]+){0,3},?\s+\d{1,4}\b"
                            r"|\b(?i:c/o|presso)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b|\b(?i:res\.)\s+\w+"),
}
# Email istituzionali e di progetto sono attese: non segnalarle.
EMAIL_AMMESSE = re.compile(r"@(unica\.it|[\w-]*\.unica\.it|example\.(com|org)|zenodo\.org|github\.com)$", re.IGNORECASE)


def scansiona(percorso: Path, massimo: int) -> int:
    file = [percorso] if percorso.is_file() else sorted(
        p for p in percorso.rglob("*") if p.is_file() and p.suffix.lower() in ESTENSIONI)
    totale = 0
    for f in file:
        testo = f.read_text(encoding="utf-8", errors="replace")
        for tipo, rx in CONTROLLI.items():
            trovati = [m.group(0) for m in rx.finditer(testo)]
            if tipo == "email":
                trovati = [t for t in trovati if not EMAIL_AMMESSE.search(t)]
            if not trovati:
                continue
            totale += len(trovati)
            esempi = "; ".join(dict.fromkeys(t.strip() for t in trovati))
            print(f"{f}: {tipo} × {len(trovati)} → {esempi[:300]}")
            if totale >= massimo * 50:
                print("… troppi risultati, interrompo")
                return totale
    return totale


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("percorso", type=Path)
    parser.add_argument("--max", type=int, default=20)
    args = parser.parse_args()
    n = scansiona(args.percorso, args.max)
    print(f"\nTotale segnalazioni: {n}" if n else "Nessuna segnalazione.")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()

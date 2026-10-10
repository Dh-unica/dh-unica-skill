#!/usr/bin/env python3
"""Profilo rapido di dati tabellari (CSV, TSV, XLSX, JSON) per il triage.

Per ogni tabella riporta: righe, colonne, e per colonna tipo prevalente,
valori mancanti, valori distinti, esempi; segnala duplicati esatti, colonne
che sembrano ID (e se sono uniche), coordinate fuori intervallo e formati
di data/periodo eterogenei.

Uso:
  python3 -I profila_dati.py <file o cartella> [--json report.json]

Solo libreria standard (XLSX letto come zip/XML).
"""
import argparse
import csv
import io
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

RX_ANNO = re.compile(r"^\s*(1[0-9]{3}|20[0-9]{2})\s*$")
RX_DATA_ISO = re.compile(r"^\s*\d{4}-\d{2}-\d{2}")
RX_DATA_IT = re.compile(r"^\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\s*$")
RX_SECOLO = re.compile(r"\b(sec(olo|\.)?|[XVI]{1,5}\s*sec)", re.IGNORECASE)
RX_INTERVALLO = re.compile(r"^\s*\d{3,4}\s*[-–/]\s*\d{2,4}\s*$")
RX_NUMERO = re.compile(r"^\s*-?\d+([.,]\d+)?\s*$")
VUOTI = {"", "nd", "n.d.", "na", "n/a", "null", "none", "-", "?"}


def leggi_csv(percorso: Path) -> list[dict]:
    testo = percorso.read_text(encoding="utf-8-sig", errors="replace")
    dialetto = csv.Sniffer().sniff(testo[:4096], delimiters=",;\t") if testo.strip() else csv.excel
    return list(csv.DictReader(io.StringIO(testo), dialect=dialetto))


def _locale(tag: str) -> str:
    """Nome del tag senza namespace (gli XLSX usano sia 'c' sia 'x:c')."""
    return tag.rsplit("}", 1)[-1]


def _testo(elemento) -> str:
    return "".join(e.text or "" for e in elemento.iter() if _locale(e.tag) == "t")


def _indice_colonna(rif: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", rif).group(0):
        n = n * 26 + ord(ch) - 64
    return n


def leggi_xlsx(percorso: Path) -> dict[str, list[dict]]:
    """Legge tutti i fogli di un XLSX senza dipendenze (valori calcolati, non formule).

    L'intestazione è la riga con più celle piene tra le prime 15: i fogli di
    lavoro hanno spesso righe di titolo o istruzioni sopra la tabella.
    """
    z = zipfile.ZipFile(percorso)
    nomi_file = set(z.namelist())
    condivise = []
    if "xl/sharedStrings.xml" in nomi_file:
        radice = ET.fromstring(z.read("xl/sharedStrings.xml"))
        condivise = [_testo(si) for si in radice if _locale(si.tag) == "si"]
    libro = ET.fromstring(z.read("xl/workbook.xml"))
    nomi = [e.get("name") for e in libro.iter() if _locale(e.tag) == "sheet"]
    fogli = {}
    for i, nome in enumerate(nomi, start=1):
        voce = f"xl/worksheets/sheet{i}.xml"
        if voce not in nomi_file:
            continue
        righe = []
        for riga in (e for e in ET.fromstring(z.read(voce)).iter() if _locale(e.tag) == "row"):
            celle = {}
            for c in riga:
                if _locale(c.tag) != "c" or not c.get("r"):
                    continue
                tipo = c.get("t")
                v = next((e.text for e in c if _locale(e.tag) == "v"), None)
                if tipo == "s" and v is not None:
                    valore = condivise[int(v)]
                elif tipo == "inlineStr":
                    valore = _testo(c)
                else:
                    valore = v or ""
                celle[_indice_colonna(c.get("r"))] = valore.strip()
            righe.append(celle)
        if not righe:
            continue
        candidati = righe[:15]
        h = max(range(len(candidati)), key=lambda k: sum(1 for v in candidati[k].values() if v))
        intestazione = {k: v for k, v in righe[h].items() if v}
        fogli[nome] = [{intestazione[k]: r.get(k, "") for k in sorted(intestazione)}
                       for r in righe[h + 1:] if any(r.values())]
    return fogli


def leggi_json(percorso: Path) -> dict[str, list[dict]]:
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    if isinstance(dati, list):
        return {percorso.stem: [d for d in dati if isinstance(d, dict)]}
    if isinstance(dati, dict):
        return {f"{percorso.stem}.{k}": [d for d in v if isinstance(d, dict)]
                for k, v in dati.items() if isinstance(v, list) and v and isinstance(v[0], dict)}
    return {}


def tipo_valore(v: str) -> str:
    if v[:1] in "[{":
        return "annidato"
    if RX_ANNO.match(v):
        return "anno"
    if RX_DATA_ISO.match(v):
        return "data_iso"
    if RX_DATA_IT.match(v):
        return "data_it"
    if RX_INTERVALLO.match(v):
        return "intervallo"
    if RX_SECOLO.search(v):
        return "secolo"
    if RX_NUMERO.match(v):
        return "numero"
    if v.startswith(("http://", "https://")):
        return "url"
    return "testo"


def profila_tabella(nome: str, righe: list[dict]) -> dict:
    colonne = list(righe[0].keys()) if righe else []
    profilo = {"tabella": nome, "righe": len(righe), "colonne": len(colonne),
               "duplicati_esatti": len(righe) - len({json.dumps(r, sort_keys=True) for r in righe}),
               "campi": [], "avvisi": []}
    for col in colonne:
        valori = [json.dumps(r[col], ensure_ascii=False) if isinstance(r.get(col), (list, dict))
                  else str(r.get(col) or "").strip() for r in righe]
        pieni = [v for v in valori if v.lower() not in VUOTI]
        tipi = Counter(tipo_valore(v) for v in pieni)
        campo = {"nome": col, "mancanti": len(valori) - len(pieni),
                 "distinti": len(set(pieni)), "tipi": dict(tipi.most_common()),
                 "esempi": [e if len(e) <= 80 else e[:77] + "…" for e in list(dict.fromkeys(pieni))[:3]]}
        profilo["campi"].append(campo)
        nome_l = col.lower()
        if nome_l in {"id", "codice"} or nome_l.startswith("id_") or nome_l.endswith("_id"):
            if len(set(pieni)) < len(pieni):
                profilo["avvisi"].append(f"'{col}' sembra un ID ma ha {len(pieni) - len(set(pieni))} valori ripetuti")
        if nome_l in {"lat", "latitudine", "geo:lat"} or nome_l in {"lon", "lng", "longitudine", "geo:long"}:
            limite = 90 if "lat" in nome_l else 180
            fuori = [v for v in pieni if RX_NUMERO.match(v) and abs(float(v.replace(",", "."))) > limite]
            if fuori or campo["mancanti"]:
                profilo["avvisi"].append(f"'{col}': {campo['mancanti']} mancanti, {len(fuori)} fuori intervallo")
        formati_tempo = {t for t in tipi if t in {"anno", "data_iso", "data_it", "intervallo", "secolo"}}
        if len(formati_tempo) > 1:
            profilo["avvisi"].append(f"'{col}': formati temporali misti {sorted(formati_tempo)}")
    if profilo["duplicati_esatti"]:
        profilo["avvisi"].append(f"{profilo['duplicati_esatti']} righe duplicate esatte")
    return profilo


def raccogli(percorso: Path) -> dict[str, list[dict]]:
    tabelle = {}
    file = [percorso] if percorso.is_file() else sorted(p for p in percorso.rglob("*") if p.is_file())
    for f in file:
        try:
            if f.suffix.lower() in {".csv", ".tsv"}:
                tabelle[str(f.name)] = leggi_csv(f)
            elif f.suffix.lower() == ".xlsx":
                tabelle.update({f"{f.name}:{k}": v for k, v in leggi_xlsx(f).items()})
            elif f.suffix.lower() == ".json":
                tabelle.update(leggi_json(f))
        except Exception as errore:  # un file illeggibile non deve fermare il triage
            print(f"[avviso] {f}: {errore}", file=sys.stderr)
    return tabelle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("percorso", type=Path)
    parser.add_argument("--json", type=Path, help="salva il profilo completo in JSON")
    args = parser.parse_args()

    profili = [profila_tabella(n, r) for n, r in raccogli(args.percorso).items()]
    for p in profili:
        print(f"\n## {p['tabella']}: {p['righe']} righe × {p['colonne']} colonne")
        for c in p["campi"]:
            tipi = ", ".join(f"{k} {v}" for k, v in c["tipi"].items())
            print(f"  - {c['nome']}: mancanti {c['mancanti']}, distinti {c['distinti']} | {tipi} | es. {c['esempi']}")
        for a in p["avvisi"]:
            print(f"  ! {a}")
    if args.json:
        args.json.write_text(json.dumps(profili, ensure_ascii=False, indent=1), encoding="utf-8")
    if not profili:
        print("Nessuna tabella trovata (CSV, TSV, XLSX, JSON).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Scarica record Zenodo (per ID, DOI o ricerca) con manifest e verifica md5.

Esempi:
  python3 -I zenodo_fetch.py --record 22810570 --out dati/raw
  python3 -I zenodo_fetch.py --doi 10.5281/zenodo.22810570 --out dati/raw
  python3 -I zenodo_fetch.py --community dhunica --query almanacco --out dati/raw --solo-metadati

Idempotente: i file già presenti con md5 corretto non vengono riscaricati.
Il manifest (manifest.json nella cartella di output) riporta record, DOI,
titolo, data, licenza, file, dimensione, md5, URL e data di download.
Solo libreria standard.
"""
import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://zenodo.org/api/records"
UA = {"User-Agent": "dh-pubblica-dataset/1.0 (ricerca DH UNICA)"}


def leggi_json(url: str, tentativi: int = 4) -> dict:
    for n in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception:
            if n == tentativi - 1:
                raise
            time.sleep(2 ** n)
    return {}


def cerca(community: str | None, query: str | None) -> list[dict]:
    """Pagina la ricerca (max 25 risultati per pagina senza autenticazione)."""
    risultati, pagina = [], 1
    while True:
        parametri = {"size": 25, "page": pagina}
        if community:
            parametri["communities"] = community
        if query:
            parametri["q"] = query
        dati = leggi_json(f"{API}?{urllib.parse.urlencode(parametri)}")
        voci = dati.get("hits", {}).get("hits", [])
        risultati.extend(voci)
        if len(risultati) >= dati.get("hits", {}).get("total", 0) or not voci:
            return risultati
        pagina += 1
        time.sleep(1)


def md5(percorso: Path) -> str:
    h = hashlib.md5()
    with percorso.open("rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def scarica(url: str, destinazione: Path, atteso: str) -> str:
    if destinazione.exists() and md5(destinazione) == atteso:
        return "presente"
    parziale = destinazione.with_suffix(destinazione.suffix + ".part")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, parziale.open("wb") as f:
        while blocco := r.read(1 << 20):
            f.write(blocco)
    if md5(parziale) != atteso:
        parziale.unlink()
        raise ValueError(f"md5 non corrispondente per {destinazione.name}")
    parziale.rename(destinazione)
    return "scaricato"


def voce_manifest(record: dict) -> dict:
    m = record.get("metadata", {})
    return {
        "record_id": record.get("id"), "doi": record.get("doi"), "titolo": m.get("title"),
        "data_pubblicazione": m.get("publication_date"), "licenza": (m.get("license") or {}).get("id"),
        "autori": [c.get("name") for c in m.get("creators", [])],
        "file": [{"nome": f["key"], "byte": f["size"], "md5": f["checksum"].split(":")[-1],
                  "url": f["links"]["self"]} for f in record.get("files", [])],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    gruppo = parser.add_mutually_exclusive_group(required=True)
    gruppo.add_argument("--record", help="ID numerico del record")
    gruppo.add_argument("--doi", help="DOI Zenodo (10.5281/zenodo.N)")
    gruppo.add_argument("--query", help="testo di ricerca")
    parser.add_argument("--community", help="limita la ricerca a una community")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--solo-metadati", action="store_true", help="scrive il manifest senza scaricare i file")
    args = parser.parse_args()

    if args.record or args.doi:
        rid = args.record or args.doi.rsplit(".", 1)[-1]
        record = [leggi_json(f"{API}/{rid}")]
    else:
        record = cerca(args.community, args.query)

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "record": []}
    for r in record:
        voce = voce_manifest(r)
        if not args.solo_metadati:
            cartella = args.out / str(voce["record_id"])
            cartella.mkdir(exist_ok=True)
            for f in voce["file"]:
                f["esito"] = scarica(f["url"], cartella / f["nome"], f["md5"])
                print(f"{voce['record_id']} {f['nome']}: {f['esito']}")
                time.sleep(0.5)
        manifest["record"].append(voce)
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(manifest['record'])} record → {args.out / 'manifest.json'}")


if __name__ == "__main__":
    main()

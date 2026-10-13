"""CLI: python -m dhmigrate <comando> --config config/<progetto>.yaml"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import ConfigError, load_config, validate
from .extract import extract
from .http import make_session
from .load import load, open_state, publish, rollback
from .menu import sync_menu
from .navsection import sync_section_nav
from .transform import transform_site
from .redirects import write_redirects
from .survey import run_survey
from .verify import verify
from .wp_client import WPClient, WPError, load_credentials

log = logging.getLogger("dhmigrate")


def cmd_login(args) -> int:
    """Salva l'Application Password in ~/.config/dh-unica/wp-<ambito>.env dopo averla verificata.

    Va eseguito dall'utente nel proprio terminale (in Claude Code: prefisso `!`), così la
    password non passa mai nella conversazione.
    """
    import getpass
    from urllib.parse import urlparse

    from .wp_client import Credentials, default_credentials_path, save_credentials

    url = args.url.rstrip("/")
    ambito = urlparse(url).netloc.split(".")[0]
    path = Path(args.credentials).expanduser() if args.credentials else default_credentials_path(ambito)
    user = input(f"Utente WordPress su {url}: ").strip()
    password = getpass.getpass("Application Password (non viene mostrata): ").strip()
    me = WPClient(url, Credentials(user, password), make_session()).me()
    caps = me.get("capabilities", {})
    save_credentials(path, url, Credentials(user, password))
    print(f"OK: credenziali di '{me.get('username')}' {me.get('roles')} salvate in {path} (permessi 600)")
    if not caps.get("edit_theme_options"):
        print("Attenzione: questo utente non può modificare i menu (serve un amministratore del sito).")
    return 0


def cmd_survey(args) -> int:
    """Ricognizione: non richiede config, la propone."""
    from .wp_client import default_credentials_path

    creds_path = Path(args.credentials).expanduser() if args.credentials else default_credentials_path(args.ambito)
    try:
        creds = load_credentials(creds_path)
    except WPError:
        creds = None
    shown = args.credentials or f"~/.config/dh-unica/wp-{args.ambito}.env"
    sv, _, report = run_survey(args.source, args.slug, args.ambito, make_session(), creds, Path(args.workdir), shown)
    print(report.read_text(encoding="utf-8"))
    print(f"config proposta: {report.parent / 'config.proposta.yaml'}")
    return 1 if any(i.startswith("CONFLITTO") for i in sv.issues) else 0


def cmd_check(cfg, args) -> int:
    errors = validate(cfg)
    for p in cfg.ordered_pages():
        print(f"{p.source_slug:28} -> {cfg.target_link(p.source_slug)}")
    print("OK: config conforme alla name convention" if not errors else "\n".join(errors))
    return 1 if errors else 0


def cmd_extract(cfg, args) -> int:
    print(json.dumps(extract(cfg, make_session()), indent=2))
    return 0


def cmd_transform(cfg, args) -> int:
    results = transform_site(cfg)
    for slug, res in results.items():
        print(f"{slug:28} blocchi={res.content.count('<!-- wp:'):4} media={len(res.media):3} avvisi={len(res.warnings)}")
        for w in res.warnings:
            print(f"    ! {w}")
    return 0


def _client(cfg, args) -> WPClient:
    return WPClient(cfg.target_url, load_credentials(cfg.credentials), make_session(), dry_run=args.dry_run)


def _confirmed(args, action: str) -> bool:
    if args.yes or args.dry_run:
        return True
    print(f"'{action}' scrive sul sito di produzione: ripetere con --yes per confermare", file=sys.stderr)
    return False


def cmd_load(cfg, args) -> int:
    result = load(cfg, _client(cfg, args), make_session(), status=args.status)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_publish(cfg, args) -> int:
    if not _confirmed(args, "publish"):
        return 1
    print(json.dumps(publish(cfg, _client(cfg, args)), indent=2, ensure_ascii=False))
    return 0


def cmd_menu(cfg, args) -> int:
    if not _confirmed(args, "menu"):
        return 1
    client = _client(cfg, args)
    state = open_state(cfg, client)
    # navigazione completa: voci nel menu globale + barra/testata del progetto (pattern sincronizzato)
    result = {**sync_menu(cfg, client, state), "section_nav": sync_section_nav(cfg, client, state)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_rollback(cfg, args) -> int:
    if not _confirmed(args, "rollback"):
        return 1
    print(json.dumps(rollback(cfg, _client(cfg, args), delete_media=not args.keep_media), indent=2))
    return 0


def cmd_verify(cfg, args) -> int:
    checks = verify(cfg, WPClient(cfg.target_url, load_credentials(cfg.credentials), make_session()), make_session())
    for c in checks:
        print(f"{'OK  ' if c.ok else 'FAIL'} {c.coverage:6.1%} {c.status:8} {c.url}")
        for f in c.failures:
            print(f"     ! {f}")
        for w in c.warnings:
            print(f"     ~ {w}")
    print(f"report: {cfg.project_dir / 'verify-report.md'}")
    return 0 if all(c.ok for c in checks) else 4


def cmd_redirects(cfg, args) -> int:
    out = Path(args.out)
    for name in write_redirects(cfg, out):
        print(out / name)
    return 0


COMMANDS = {
    "check": cmd_check,
    "extract": cmd_extract,
    "transform": cmd_transform,
    "load": cmd_load,
    "publish": cmd_publish,
    "rollback": cmd_rollback,
    "menu": cmd_menu,
    "verify": cmd_verify,
    "redirects": cmd_redirects,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dhmigrate", description="Migrazione minisiti nei portali DH UniCA")
    parser.add_argument("command", choices=sorted([*COMMANDS, "survey", "login"]))
    parser.add_argument("--url", help="login: URL del portale DH di destinazione")
    parser.add_argument("--config", help="config YAML del progetto (tutti i comandi tranne survey)")
    parser.add_argument("--source", help="survey: URL del minisito sorgente")
    parser.add_argument("--slug", help="survey: slug di progetto (name convention)")
    parser.add_argument("--ambito", help="survey: sottodominio DH (storia, musica, cinema, ...)")
    parser.add_argument("--credentials", help="login/survey: file credenziali (default ~/.config/dh-unica/wp-<ambito>.env)")
    parser.add_argument("--workdir", default="work", help="survey: cartella di lavoro")
    parser.add_argument("--dry-run", action="store_true", help="nessuna scrittura sulla destinazione")
    parser.add_argument("--status", default="draft", choices=["draft", "publish"], help="stato pagine in load")
    parser.add_argument("--yes", action="store_true", help="conferma publish/rollback")
    parser.add_argument("--keep-media", action="store_true", help="rollback: non eliminare i media")
    parser.add_argument("--out", default="docs", help="redirects: cartella di output")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    if args.command == "login":
        if not args.url:
            parser.error("login richiede --url (es. https://storia.dh.unica.it)")
        try:
            return cmd_login(args)
        except WPError as exc:
            print(f"Credenziali non valide: {exc}", file=sys.stderr)
            return 3
    if args.command == "survey":
        if not (args.source and args.slug and args.ambito):
            parser.error("survey richiede --source, --slug e --ambito")
        try:
            return cmd_survey(args)
        except (ValueError, WPError) as exc:
            print(f"Ricognizione fallita: {exc}", file=sys.stderr)
            return 2
    if not args.config:
        parser.error("--config è obbligatorio per questo comando")
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"Config non valida: {exc}", file=sys.stderr)
        return 2
    try:
        return COMMANDS[args.command](cfg, args)
    except WPError as exc:
        print(f"Errore WordPress: {exc}", file=sys.stderr)
        return 3

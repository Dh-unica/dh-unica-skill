#!/usr/bin/env python3
"""Verifica che il marketplace dh-unica-skill rispetti lo standard DH (vedi CONTRIBUTING.md).

Uso:  python3 check_skills.py [radice-marketplace]     (default: cartella corrente)
Esce con 1 se trova errori, 0 altrimenti. Gli avvisi non bloccano.

Dipendenze: solo libreria standard + PyYAML (per il frontmatter delle skill).
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PLUGIN_NAME_RE = re.compile(r"^dh-[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
LEVEL_RE = re.compile(r"\*\*Livello:\*\*\s*(sola lettura|bozze|produzione)", re.I)

# Campi del frontmatter SKILL.md documentati da Claude Code: un campo sconosciuto viene ignorato
# in silenzio (es. `trigger`), quindi lo trattiamo come errore.
KNOWN_FIELDS = {
    "name", "description", "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
    "user-invocable", "allowed-tools", "disallowed-tools", "model", "effort", "context", "agent",
    "hooks", "paths", "shell", "metadata", "license", "compatibility",
}
MAX_LISTING = 1536  # description + when_to_use oltre questa lunghezza vengono troncati

README_SECTIONS = [
    "Cosa fa",
    "Quando usarla",
    "Installazione",
    "Prerequisiti",
    "Come si avvia",
    "Domande che ti farà",
    "Cosa modifica",
    "Come tornare indietro",
    "Sicurezza e dati personali",
    "Limiti noti",
    "Manutenzione",
]

SECRET_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9]{4}(?: [A-Za-z0-9]{4}){5}\b"), "possibile Application Password WordPress"),
    (re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[=:]\s*['\"]?[A-Za-z0-9/+_\-]{12,}"),
     "possibile credenziale in chiaro"),
    (re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"), "chiave privata"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"), "token GitHub"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "chiave API"),
]
TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".toml", ".html", ".js", ".css"}
# segnaposto innocui che somigliano a password (es. negli esempi della documentazione)
SECRET_ALLOWLIST = re.compile(r"xxxx|XXXX|<[^>]+>|\.\.\.")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def load_json(path: Path, report: Report) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(str(path), "file mancante")
    except json.JSONDecodeError as exc:
        report.error(str(path), f"JSON non valido: {exc}")
    return None


def check_frontmatter(skill_dir: Path, report: Report) -> dict | None:
    where = str(skill_dir / "SKILL.md")
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        report.error(where, "frontmatter YAML assente (deve iniziare con ---)")
        return None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        report.error(where, f"frontmatter non è YAML valido (usa `>-` per testi con i due punti): {exc}")
        return None
    unknown = set(data) - KNOWN_FIELDS
    if unknown:
        report.error(where, f"campi non supportati da Claude Code (vengono ignorati): {sorted(unknown)}")
    if data.get("name") != skill_dir.name:
        report.error(where, f"name '{data.get('name')}' diverso dal nome della cartella '{skill_dir.name}'")
    if not data.get("description"):
        report.error(where, "description mancante")
    if not data.get("when_to_use"):
        report.error(where, "when_to_use mancante: indica quando attivarla e quando NO")
    listing = len(str(data.get("description", ""))) + len(str(data.get("when_to_use", "")))
    if listing > MAX_LISTING:
        report.error(where, f"description + when_to_use = {listing} caratteri (max {MAX_LISTING})")
    return data


def check_skill_references(skill_dir: Path, plugin_dir: Path, report: Report) -> None:
    where = str(skill_dir / "SKILL.md")
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    for ref in re.findall(r"`((?:references|assets|scripts)/[\w./-]+)`", text):
        if not (skill_dir / ref).exists():
            report.error(where, f"riferimento a file inesistente: {ref}")
    for ref in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)", text):
        if not (skill_dir / ref).exists():
            report.error(where, f"riferimento a file inesistente: ${{CLAUDE_SKILL_DIR}}/{ref}")
    for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", text):
        if not (plugin_dir / ref.rstrip("/")).exists():
            report.error(where, f"riferimento a file inesistente: ${{CLAUDE_PLUGIN_ROOT}}/{ref}")
    if re.search(r"~/\.claude/skills/[\w-]", text):
        report.error(where, "percorso fisso ~/.claude/skills/: usa ${CLAUDE_SKILL_DIR} o ${CLAUDE_PLUGIN_ROOT}")


def check_readme(plugin_dir: Path, report: Report) -> None:
    where = str(plugin_dir / "README.md")
    path = plugin_dir / "README.md"
    if not path.exists():
        report.error(where, "README.md mancante (usa il modello di crea-skill)")
        return
    text = path.read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+?)\s*$", text, re.M)
    missing = [s for s in README_SECTIONS if s not in headings]
    if missing:
        report.error(where, f"sezioni mancanti: {missing}")
    present = [h for h in headings if h in README_SECTIONS]
    if not missing and present != README_SECTIONS:
        report.error(where, "le sezioni standard non sono nell'ordine previsto")
    if not LEVEL_RE.search(text):
        report.error(where, "in «Cosa modifica» manca '**Livello:** sola lettura | bozze | produzione'")
    if "TODO" in text:
        report.warn(where, "contiene ancora dei TODO")


def check_changelog(plugin_dir: Path, version: str, report: Report) -> None:
    where = str(plugin_dir / "CHANGELOG.md")
    path = plugin_dir / "CHANGELOG.md"
    if not path.exists():
        report.error(where, "CHANGELOG.md mancante")
    elif f"## [{version}]" not in path.read_text(encoding="utf-8"):
        report.error(where, f"nessuna voce '## [{version}]' per la versione corrente di plugin.json")


def check_secrets(root: Path, report: Report) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or ".git" in path.parts:
            continue
        if any(part in {".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for pattern, label in SECRET_PATTERNS:
                found = pattern.search(line)
                if found and not SECRET_ALLOWLIST.search(found.group(0)):
                    report.error(f"{path.relative_to(root)}:{lineno}", f"{label}: rimuovila e revocala")


def check_plugin(root: Path, entry: dict, report: Report) -> None:
    name = entry.get("name", "?")
    where = f"plugin {name}"
    if not PLUGIN_NAME_RE.match(name):
        report.error(where, "nome non conforme: dh-<area> in minuscolo con trattini (es. dh-siti)")
    source = entry.get("source")
    if not isinstance(source, str) or not source.startswith("./"):
        report.warn(where, "source non locale: i controlli sul contenuto vengono saltati")
        return
    plugin_dir = (root / source).resolve()
    if not plugin_dir.is_dir():
        report.error(where, f"cartella {source} inesistente")
        return
    manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json", report)
    if manifest is None:
        return
    if manifest.get("name") != name:
        report.error(where, f"name in plugin.json ('{manifest.get('name')}') diverso dal marketplace")
    version = manifest.get("version", "")
    if not SEMVER_RE.match(version):
        report.error(where, f"version '{version}' non è semver (es. 1.2.0)")
    if "version" in entry:
        report.error(where, "version anche nel marketplace: tienila solo in plugin.json")
    for key in ("description", "author"):
        if not manifest.get(key):
            report.error(where, f"plugin.json senza '{key}'")
    check_readme(plugin_dir, report)
    check_changelog(plugin_dir, version, report)
    skills_dir = plugin_dir / "skills"
    skills = sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []
    if not skills:
        report.error(where, "nessuna skill in skills/")
    for skill_dir in skills:
        if not (skill_dir / "SKILL.md").exists():
            report.error(str(skill_dir), "SKILL.md mancante")
            continue
        if not SKILL_NAME_RE.match(skill_dir.name):
            report.error(str(skill_dir), "nome skill non in kebab-case minuscolo")
        if skill_dir.name.startswith("dh-") or skill_dir.name.endswith("-dh"):
            report.error(str(skill_dir), "il nome della skill non ripete 'dh': lo porta già il plugin (dh-<area>:<skill>)")
        check_frontmatter(skill_dir, report)
        check_skill_references(skill_dir, plugin_dir, report)


def check_marketplace(root: Path) -> Report:
    report = Report()
    market = load_json(root / ".claude-plugin" / "marketplace.json", report)
    if market is None:
        return report
    for key in ("name", "owner", "plugins"):
        if key not in market:
            report.error("marketplace.json", f"campo obbligatorio '{key}' mancante")
    names = [p.get("name") for p in market.get("plugins", [])]
    if len(names) != len(set(names)):
        report.error("marketplace.json", "nomi di plugin duplicati")
    for entry in market.get("plugins", []):
        check_plugin(root, entry, report)
    index = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    for name in names:
        if f"`{name}`" not in index:
            report.warn("README.md", f"il plugin `{name}` non compare nell'indice")
    check_secrets(root, report)
    return report


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    report = check_marketplace(root)
    for w in report.warnings:
        print(f"AVVISO  {w}")
    for e in report.errors:
        print(f"ERRORE  {e}")
    print(f"\n{len(report.errors)} errori, {len(report.warnings)} avvisi")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

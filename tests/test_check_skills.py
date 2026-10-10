import json

from .conftest import ROOT, check_skills


def errors(root):
    return check_skills.check_marketplace(root).errors


def test_marketplace_reale_conforme():
    report = check_skills.check_marketplace(ROOT)
    assert report.errors == [], report.errors


def test_campo_trigger_non_supportato(market):
    skill = market / "plugins/dh-siti/skills/migrazione-minisito/SKILL.md"
    skill.write_text(skill.read_text().replace("argument-hint:", "trigger: /x\nargument-hint:", 1))
    assert any("campi non supportati" in e and "trigger" in e for e in errors(market))


def test_frontmatter_non_yaml(market):
    skill = market / "plugins/dh-strumenti/skills/crea-skill/SKILL.md"
    text = skill.read_text()
    start = text.index("description: >-")
    end = text.index("when_to_use:")
    skill.write_text(text[:start] + "description: Fa questo: e anche quello: rotto\n" + text[end:])
    assert any("non è YAML valido" in e for e in errors(market))


def test_nome_skill_con_dh_e_nome_diverso_dalla_cartella(market):
    src = market / "plugins/dh-strumenti/skills/crea-skill"
    src.rename(src.parent / "crea-skill-dh")
    errs = errors(market)
    assert any("non ripete 'dh'" in e for e in errs)
    assert any("diverso dal nome della cartella" in e for e in errs)


def test_nome_plugin_non_conforme(market):
    path = market / ".claude-plugin/marketplace.json"
    data = json.loads(path.read_text())
    data["plugins"][0]["name"] = "Siti"
    path.write_text(json.dumps(data))
    assert any("nome non conforme" in e for e in errors(market))


def test_readme_sezione_mancante_e_livello(market):
    readme = market / "plugins/dh-siti/README.md"
    text = readme.read_text().replace("## Limiti noti", "## Limiti").replace("**Livello:**", "Livello:")
    readme.write_text(text)
    errs = errors(market)
    assert any("sezioni mancanti" in e and "Limiti noti" in e for e in errs)
    assert any("Livello" in e for e in errs)


def test_changelog_senza_versione_corrente(market):
    manifest = market / "plugins/dh-siti/.claude-plugin/plugin.json"
    data = json.loads(manifest.read_text())
    data["version"] = "9.9.9"
    manifest.write_text(json.dumps(data))
    assert any("9.9.9" in e for e in errors(market))


def test_version_non_semver_e_duplicata_nel_marketplace(market):
    path = market / ".claude-plugin/marketplace.json"
    data = json.loads(path.read_text())
    data["plugins"][0]["version"] = "1"
    path.write_text(json.dumps(data))
    manifest = market / "plugins/dh-siti/.claude-plugin/plugin.json"
    m = json.loads(manifest.read_text())
    m["version"] = "1.0"
    manifest.write_text(json.dumps(m))
    errs = errors(market)
    assert any("non è semver" in e for e in errs) and any("solo in plugin.json" in e for e in errs)


def test_riferimenti_inesistenti_e_percorsi_fissi(market):
    skill = market / "plugins/dh-siti/skills/ricognizione-minisito/SKILL.md"
    skill.write_text(skill.read_text() + "\nVedi `references/manca.md`, ${CLAUDE_PLUGIN_ROOT}/scripts/manca.sh "
                     "e ~/.claude/skills/x.\n")
    errs = " ".join(errors(market))
    assert "references/manca.md" in errs and "scripts/manca.sh" in errs and "percorso fisso" in errs


def test_segreti_bloccati(market):
    fake_app_password = " ".join(["Ab3d"] * 6)  # costruita a runtime: il file non contiene segreti
    (market / "plugins/dh-siti/note.md").write_text(f"chiave: {fake_app_password}\n"
                                                    "token = ghp_" + "a" * 36 + "\n")
    errs = " ".join(errors(market))
    assert "Application Password" in errs and "token GitHub" in errs


def test_segnaposto_non_sono_segreti(market):
    (market / "plugins/dh-siti/note.md").write_text('WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"\n')
    assert errors(market) == []


def test_main_codici_di_uscita(market, capsys):
    assert check_skills.main(["x", str(market)]) == 0
    (market / "plugins/dh-siti/CHANGELOG.md").unlink()
    assert check_skills.main(["x", str(market)]) == 1
    assert "CHANGELOG.md mancante" in capsys.readouterr().out

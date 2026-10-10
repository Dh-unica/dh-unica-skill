import json

import pytest

from .conftest import check_skills, scaffold


def run(market, **kw):
    args = {"plugin": "dh-prova", "skill": "esempio-prova", "skill_descrizione": "Pubblica un dataset. Bene.",
            "livello": "bozze", "plugin_descrizione": "Dati di ricerca del DH."} | kw
    argv = ["--root", str(market)]
    for key, value in args.items():
        argv += [f"--{key.replace('_', '-')}", value]
    return scaffold.main(argv)


def test_nuovo_plugin_e_skill(market):
    assert run(market) == 0
    plugin = market / "plugins/dh-prova"
    assert json.loads((plugin / ".claude-plugin/plugin.json").read_text())["name"] == "dh-prova"
    assert (plugin / "skills/esempio-prova/SKILL.md").exists()
    names = [p["name"] for p in json.loads((market / ".claude-plugin/marketplace.json").read_text())["plugins"]]
    assert names == sorted(names) and "dh-prova" in names
    assert "`/dh-prova:esempio-prova`" in (market / "README.md").read_text()
    report = check_skills.check_marketplace(market)
    assert report.errors == [], report.errors          # struttura già conforme
    assert any("TODO" in w for w in report.warnings)   # ma da completare


def test_skill_in_plugin_esistente(market):
    assert run(market, plugin="dh-siti", skill="verifica-link", plugin_descrizione="") == 0
    readme = (market / "plugins/dh-siti/README.md").read_text()
    assert "| `verifica-link` | `/dh-siti:verifica-link` | bozze |" in readme
    assert check_skills.check_marketplace(market).errors == []


def test_non_sovrascrive_skill_esistente(market):
    assert run(market, plugin="dh-siti", skill="migrazione-minisito") == 1


@pytest.mark.parametrize("kw", [{"plugin": "siti"}, {"skill": "dh-pubblica"}, {"skill": "Pubblica_Dati"},
                                {"plugin": "dh-nuovo", "plugin_descrizione": ""}])
def test_nomi_non_conformi_rifiutati(market, kw):
    with pytest.raises(SystemExit):
        run(market, **kw)

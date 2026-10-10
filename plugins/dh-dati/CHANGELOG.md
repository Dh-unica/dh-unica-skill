# Changelog: dh-dati

Formato: [Keep a Changelog](https://keepachangelog.com/it/1.1.0/), versioni [SemVer](https://semver.org/lang/it/).
Ogni modifica pubblicata incrementa `version` in `.claude-plugin/plugin.json`: senza, i collaboratori
non ricevono l'aggiornamento.

## [1.0.0] - 2026-10-10

### Aggiunto
- Skill `pubblicazione-dataset`, portata nello standard DH dalla skill `dh-pubblica-dataset` del
  progetto *Almanacco della Sardegna* (commit `00a40b4`, già collaudata): metodo in sette fasi,
  riferimenti, script (profilo dati, testo da PDF, download Zenodo, controllo privacy), modelli per
  WordPress, istruzioni del revisore critico.

### Modificato
- Frontmatter diviso in `description` e `when_to_use`; regole e domande all'avvio esplicite; percorsi
  relativi a `${CLAUDE_SKILL_DIR}`. Valutazioni e cartelle di lavoro restano nel progetto d'origine.

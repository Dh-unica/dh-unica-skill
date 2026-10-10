# Changelog: dh-siti

Formato: [Keep a Changelog](https://keepachangelog.com/it/1.1.0/), versioni [SemVer](https://semver.org/lang/it/).
Ogni modifica pubblicata incrementa `version` in `.claude-plugin/plugin.json`: senza, i collaboratori
non ricevono l'aggiornamento.

## [1.0.0] - 2026-10-10

### Aggiunto
- Skill `ricognizione-minisito` (sola lettura) e `migrazione-minisito` (produzione), portate dal
  progetto `skill_migrazione_minisito_wp` e collaudate sulla migrazione di laricchezzadellachiesa.com
  in storia.dh.unica.it/laricchezzadellachiesa/.
- Strumento `dhmigrate`: survey, extract, transform, load, verify, publish, menu, redirects, rollback,
  login.
- Navigazione su due livelli: voce sotto «Progetti» nel menu del portale e barra di sezione del
  progetto (pattern sincronizzato con blocco Navigation).

### Modificato
- Nomi delle skill secondo lo standard DH (prima `migrazione-minisito-dh` e `ricognizione-minisito-dh`).
- Virtualenv in `${CLAUDE_PLUGIN_DATA}/venv`, script condivisi in `${CLAUDE_PLUGIN_ROOT}/scripts/`.

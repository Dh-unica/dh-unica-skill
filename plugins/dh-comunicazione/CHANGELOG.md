# Changelog: dh-comunicazione

Formato: [Keep a Changelog](https://keepachangelog.com/it/1.1.0/), versioni [SemVer](https://semver.org/lang/it/).
Ogni modifica pubblicata incrementa `version` in `.claude-plugin/plugin.json`: senza, i collaboratori
non ricevono l'aggiornamento.

## [1.0.0] - 2026-10-10

### Aggiunto
- Skill `creazione-slide`, portata nello standard DH dalla skill personale `dh-unica-slides`:
  renderer HTML/Marp, estrattore da .pptx/.pdf, schema del deck, esempio (deck DOG), loghi e temi.

### Modificato
- Frontmatter con `when_to_use` (il campo `triggers` non è supportato da Claude Code), percorsi con
  `${CLAUDE_SKILL_DIR}`, domande all'avvio.

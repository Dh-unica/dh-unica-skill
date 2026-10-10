---
name: {{skill}}
description: >-
  {{skill_descrizione}}
when_to_use: >-
  TODO: quando attivarla (frasi tipiche dell'utente, anche senza nominare la skill) o quando
  l'utente invoca /{{plugin}}:{{skill}}. Non usarla per: TODO.
argument-hint: "TODO"
---

# /{{plugin}}:{{skill}}

TODO: una frase sullo scopo e sul risultato atteso.

## Regole (non negoziabili)

1. **Ogni scelta variabile si chiede all'utente** con `AskUserQuestion` (massimo 4 domande per chiamata),
   proponendo un'opzione «(Consigliata)». Mai decidere al suo posto.
2. **Credenziali fuori dalla chat**: l'utente le salva da sé con un comando `!` eseguito nel proprio
   terminale; i file stanno in `~/.config/dh-unica/<servizio>.env` con permessi 600. Mai nel repository.
3. **Livello: {{livello}}.** Se la skill scrive su sistemi in produzione: prova a vuoto (dry-run),
   bozza, verifica, conferma esplicita, rollback documentato, registro di ciò che è stato creato.
4. **Git**: un branch per ogni task, commit convenzionali, merge `--no-ff` o pull request. Mai commit
   diretti su `main`.
5. Testi per l'utente in italiano corretto, con gli accenti.

## Domande all'avvio

1. TODO

## Procedura

1. TODO

I file della skill si richiamano con `${CLAUDE_SKILL_DIR}/…`; quelli condivisi del plugin con
`${CLAUDE_PLUGIN_ROOT}/…`; dati persistenti (es. virtualenv) in `${CLAUDE_PLUGIN_DATA}/…`.

## Output per l'utente

TODO: cosa riportare alla fine (breve, con link ai file prodotti e alle azioni residue).

---
name: crea-skill
description: >-
  Crea una nuova skill Claude Code per il Centro DH UNICA nel marketplace dh-unica-skill, rispettando
  lo standard DH: nomi (plugin dh-<area>, skill <azione>-<oggetto>), frontmatter valido, README con
  sezioni fisse, CHANGELOG e versione, regole su domande all'utente, credenziali e produzione,
  controlli automatici e workflow git. Parte da un'intervista, genera la struttura dai modelli,
  la completa con l'autore e la valida.
when_to_use: >-
  Quando qualcuno del DH vuole creare, impacchettare o pubblicare una skill per il DH ("facciamo una
  skill per…", "trasforma questa procedura in una skill", "aggiungi questa skill al marketplace
  dh-unica") o invoca /dh-strumenti:crea-skill. Anche per portare nello standard una skill esistente
  (es. una cartella skills/ dentro un altro repository). Non per usare skill già esistenti.
argument-hint: "[descrizione breve della skill]"
---

# /dh-strumenti:crea-skill

Crea una skill di qualità e uniforme alle altre del DH. Lo standard completo è in `CONTRIBUTING.md`
nella radice del marketplace; questa skill lo applica e lo verifica.

## Regole (non negoziabili)

1. **Si chiede, non si indovina.** Ogni scelta variabile passa da `AskUserQuestion` (massimo 4 domande
   per chiamata), sempre con un'opzione «(Consigliata)» motivata.
2. **Un'unica fonte di verità per lo standard**: i modelli in `${CLAUDE_SKILL_DIR}/assets/template/`
   e i controlli di `${CLAUDE_SKILL_DIR}/scripts/check_skills.py`. Non inventare sezioni o campi diversi.
3. **Git**: si lavora nel clone locale del marketplace, su un branch `feat/<plugin>-<skill>`.
   Commit convenzionali, merge `--no-ff` o pull request; mai commit diretti su `main`.
4. **Nessun segreto** in nessun file: `check_skills.py` blocca password, token e chiavi.

## Domande all'avvio

**Blocco 1: identità**
1. **Cosa deve fare la skill**, in una frase, e quale risultato consegna.
2. **Area / plugin**: proponi un plugin esistente se l'area combacia (leggi `.claude-plugin/marketplace.json`),
   altrimenti un nuovo `dh-<area>` (es. `dh-archivi`, `dh-dati`, `dh-didattica`).
3. **Nome della skill**: proponi `<azione>-<oggetto>` in italiano (es. `pubblicazione-dataset`), senza
   «dh» perché lo porta già il plugin. Mostra il comando risultante `/dh-<area>:<skill>`.
4. **Manutentore** (nome e cognome di chi risponde della skill).

**Blocco 2: comportamento**
5. **Quando si attiva e quando no**: frasi tipiche di un collega e casi da escludere.
6. **Livello di impatto**: *sola lettura*, *bozze* (scrive ma non pubblica) o *produzione*.
   Per *produzione* sono obbligatori: prova a vuoto, conferma esplicita, rollback e registro di ciò che
   è stato creato.
7. **Credenziali e permessi** necessari (quali servizi, quale ruolo minimo).
8. **Dati personali** trattati (nomi, foto, e-mail) e cautele.

**Blocco 3: procedura**
9. **Domande che la skill dovrà fare** ai suoi utenti (le scelte variabili del suo dominio).
10. **Passi** della procedura e **script** necessari (Python, shell), con eventuali dipendenze.

## Procedura

1. **Clone del marketplace.** Lavora nella cartella locale di `Dh-unica/dh-unica-skill` (chiedi il
   percorso se non è evidente) e crea il branch `feat/<plugin>-<skill>`.
2. **Struttura dai modelli:**
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py --root <marketplace> --plugin <dh-area> \
     --skill <azione-oggetto> --skill-descrizione "<frase>" --livello "<livello>" \
     [--plugin-descrizione "<frase>" --manutentore "<nome>" --categoria <categoria>]
   ```
   Crea `plugins/<plugin>/` (se nuovo: `plugin.json`, README, CHANGELOG), la cartella della skill e le
   righe nei cataloghi. Non sovrascrive file esistenti.
3. **Completa i TODO** con le risposte dell'intervista:
   - `SKILL.md`: `description` (cosa fa) e `when_to_use` (quando sì, quando no) sono ciò che Claude legge
     per decidere se attivarla. Scrivile concrete, con le parole degli utenti, sotto 1.536 caratteri.
     Corpo: regole, domande all'avvio, procedura, output. Per i file usa `${CLAUDE_SKILL_DIR}`,
     `${CLAUDE_PLUGIN_ROOT}` e `${CLAUDE_PLUGIN_DATA}` (virtualenv, cache), mai `~/.claude/skills/…`.
   - README del plugin: tutte le 11 sezioni standard, scritte per un collega non tecnico.
   - Testi lunghi o di riferimento in `references/`, modelli in `assets/`, codice in `scripts/`.
     Il codice ha i suoi test.
4. **Versione:** incrementa `version` in `plugin.json` (SemVer: correzione → patch, nuova skill o
   funzione → minor, cambio incompatibile → major) e aggiungi la voce nel `CHANGELOG.md`.
5. **Controlli** (devono passare entrambi):
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/check_skills.py <marketplace>
   claude plugin validate <marketplace> --strict
   ```
6. **Prova reale:** `claude plugin marketplace add <marketplace>` (cartella locale), poi
   `claude plugin install <plugin>@dh-unica-skill` e, in una nuova sessione, una richiesta tipica.
   Verifica che la skill si attivi e faccia le domande previste.
7. **Chiusura git:** commit, merge `--no-ff` su `main` (o `gh pr create` se c'è il remote), cancella il
   branch. Ricorda all'utente che i colleghi ricevono l'aggiornamento solo con la nuova `version`.

## Portare nello standard una skill esistente

Stessa intervista, ma parti dalla `SKILL.md` esistente:
- rinomina secondo la convenzione;
- sposta i campi non supportati (es. `trigger:`) in `when_to_use`;
- sostituisci i percorsi fissi con le variabili `${CLAUDE_…}`;
- scrivi README e CHANGELOG.

Le cartelle di valutazione (`*-evals`, `*-workspace`) restano nel repository d'origine e non entrano
nel plugin.

## Output per l'utente

Riepilogo breve:
- comando della skill (`/dh-<area>:<skill>`) e livello;
- file creati;
- esito dei controlli;
- comandi di installazione per i colleghi;
- cosa resta da completare (TODO residui, test, pubblicazione su GitHub).

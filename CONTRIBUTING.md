# Standard DH UNICA per le skill

Regole comuni per tutte le skill del marketplace `dh-unica-skill`. Servono a far sì che ogni skill si
installi, si presenti e si comporti allo stesso modo, e che si possa usare in sicurezza su sistemi reali.

Le regole marcate **[auto]** sono verificate da `check_skills.py`, sul tuo computer e su GitHub. La
skill `/dh-strumenti:crea-skill` le applica per te.

## 1. Nomi

| Elemento | Regola | Esempio |
|---|---|---|
| Marketplace | `dh-unica-skill` (= nome del repository) | `Dh-unica/dh-unica-skill` |
| Plugin | `dh-<area>`, minuscolo, con trattini **[auto]** | `dh-siti`, `dh-archivi`, `dh-dati`, `dh-didattica`, `dh-strumenti` |
| Skill | `<azione>-<oggetto>` in italiano, kebab-case, **senza «dh»** **[auto]** | `migrazione-minisito`, `pubblicazione-dataset` |
| Comando risultante | `/<plugin>:<skill>` | `/dh-siti:migrazione-minisito` |
| Branch git | `feat/<plugin>-<skill>`, `fix/…`, `docs/…`, `chore/…` | `feat/dh-dati-pubblicazione-dataset` |
| Credenziali | `~/.config/dh-unica/<servizio>.env`, permessi 600 | `~/.config/dh-unica/zenodo.env` |

Un plugin raggruppa le skill di una stessa area. Crea un plugin nuovo solo se nessuno esistente è
pertinente.

## 2. Struttura

```
plugins/<dh-area>/
├── .claude-plugin/plugin.json   name = cartella, version SemVer, description, author   [auto]
├── README.md                    11 sezioni standard                                      [auto]
├── CHANGELOG.md                 voce per la version corrente                             [auto]
├── scripts/                     codice condiviso tra le skill (facoltativo)
└── skills/<azione-oggetto>/
    ├── SKILL.md                 istruzioni per Claude                                    [auto]
    ├── references/              testi di riferimento, letti solo quando servono
    ├── assets/                  modelli e file da copiare
    └── scripts/                 codice della skill, con test
```

Le cartelle di lavoro e di valutazione (`work/`, `*-workspace/`, `*-evals/`) non entrano nel plugin.

## 3. SKILL.md

- **Frontmatter YAML valido** **[auto]**. Per testi con i due punti usa lo stile `>-`.
- Solo campi supportati da Claude Code **[auto]**: un campo sconosciuto (es. `trigger:`) viene
  ignorato in silenzio. Si usano almeno:
  - `name`: uguale alla cartella **[auto]**;
  - `description`: *cosa fa* e *cosa consegna*;
  - `when_to_use`: *quando attivarla*, con le parole di un collega, e *quando no* **[auto]**;
  - `argument-hint`: argomenti facoltativi del comando.
- `description` più `when_to_use` restano sotto i **1.536 caratteri** **[auto]**: oltre vengono troncati.
- **Percorsi:**
  - `${CLAUDE_SKILL_DIR}/…` per i file della skill;
  - `${CLAUDE_PLUGIN_ROOT}/…` per quelli condivisi del plugin;
  - `${CLAUDE_PLUGIN_DATA}/…` per dati persistenti (virtualenv, cache), che sopravvivono agli
    aggiornamenti;
  - mai `~/.claude/skills/…` **[auto]**;
  - i file citati devono esistere **[auto]**.
- Il corpo segue sempre questo schema:
  1. **Regole** (non negoziabili);
  2. **Domande all'avvio**;
  3. **Procedura**;
  4. **Output per l'utente**.

## 4. Comportamento

1. **Si chiede, non si indovina.** Ogni scelta variabile (nomi, posizioni, cosa includere, se
   pubblicare) passa da `AskUserQuestion`, con un'opzione «(Consigliata)» motivata. Se la risposta è già
   nella richiesta, si riporta nel riepilogo senza richiederla.
2. **Livello di impatto dichiarato** nel README **[auto]**:
   - *sola lettura*: non modifica nulla;
   - *bozze*: crea file o contenuti non pubblicati;
   - *produzione*: scrive su servizi reali.
3. **Per il livello *produzione* sono obbligatori:**
   - prova a vuoto (`--dry-run`);
   - lavoro in bozza;
   - verifica automatica del risultato;
   - **conferma esplicita** prima di pubblicare;
   - **registro** di tutto ciò che è stato creato (es. `state.json`);
   - **rollback** che tocca solo quello;
   - nessuna modifica a contenuti non creati dalla skill.
4. **Lingua:** testi per l'utente in italiano corretto, con gli accenti; termini tecnici e codice in
   originale.
5. **Git:** un branch per task, commit convenzionali (`feat:`, `fix:`, `docs:`, `chore:`…), merge
   `--no-ff` o pull request; mai commit diretti su `main`.

## 5. Credenziali e dati personali

- **Mai nella chat, mai nel repository** **[auto: password, token e chiavi vengono bloccati]**.
- L'utente salva le credenziali da sé con un comando `!` nel proprio terminale. Esempio:
  `dhmigrate login`, che chiede la password senza mostrarla, la verifica e la scrive in un file 600.
- Per server e automazioni si usano variabili d'ambiente documentate nel README.
- Si usa il ruolo minimo necessario. A fine lavoro la skill ricorda di revocare le password
  applicazione.
- Se la skill tratta dati personali (nomi, foto, contatti), il README lo dichiara e la skill ricorda di
  verificare il consenso alla pubblicazione.

## 6. README del plugin

Le 11 sezioni, in quest'ordine e con questi titoli **[auto]**:

| # | Sezione | Contenuto |
|---|---|---|
| 1 | Cosa fa | 1-2 frasi comprensibili da chi non è tecnico |
| 2 | Quando usarla | **Sì:** richieste tipiche · **No:** casi esclusi e alternative |
| 3 | Installazione | i comandi `/plugin` |
| 4 | Prerequisiti | account, ruoli, credenziali (come salvarle), software |
| 5 | Come si avvia | una frase d'esempio e il comando |
| 6 | Domande che ti farà | elenco numerato |
| 7 | Cosa modifica | `**Livello:** sola lettura / bozze / produzione` **[auto]** e dettagli |
| 8 | Come tornare indietro | rollback o «non serve» |
| 9 | Sicurezza e dati personali | credenziali e dati trattati |
| 10 | Limiti noti | casi non gestiti |
| 11 | Manutenzione | manutentore, versione, segnalazioni |

In testa al README va la tabella delle skill (`Skill | Comando | Livello`). Ogni skill ha anche una riga
nel **Catalogo** del README principale (`scaffold.py` la aggiunge da sé).

## 7. Versioni

- `version` in `plugin.json`, in **SemVer** **[auto]**, e solo lì (non nel marketplace) **[auto]**:
  - **patch** (1.0.1): correzioni;
  - **minor** (1.1.0): nuova skill o nuova funzione;
  - **major** (2.0.0): cambi incompatibili (nomi, config, comportamento).
- Ogni versione ha la sua voce `## [x.y.z] - data` nel CHANGELOG **[auto]**.
- **Senza un aumento di versione i colleghi non ricevono l'aggiornamento.**

## 8. Qualità

Prima della merge su `main`:

```bash
python3 plugins/dh-strumenti/skills/crea-skill/scripts/check_skills.py .   # standard DH
claude plugin validate . --strict                                          # formato Claude Code
python3 -m pytest -q                                                       # test del marketplace
```

Poi una **prova reale**:
1. `claude plugin marketplace add <clone-locale>`;
2. installa il plugin;
3. in una nuova sessione fai una richiesta tipica;
4. verifica che la skill si attivi e faccia le domande previste.

Le skill di livello *produzione* devono avere test sugli script e, quando possibile, un collaudo su un
sito o servizio di prova.

## 9. Licenza e revisione

- Tutto il marketplace è rilasciato con licenza **MIT** (file `LICENSE`); `plugin.json` riporta
  `"license": "MIT"`. Non includere materiali con licenze incompatibili (font, loghi di terzi, dataset).
- Ogni pull request richiede l'approvazione dei revisori indicati in `.github/CODEOWNERS`.

## 10. Codice sviluppato altrove

Se una skill porta con sé uno strumento che ha un suo repository (con i test), come `dhmigrate`, lo
sviluppo resta lì. Nel plugin si copia solo il codice necessario, con uno script di sincronizzazione
documentato nel README («Manutenzione»).

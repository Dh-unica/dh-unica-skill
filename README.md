# dh-unica-skill

Marketplace delle **skill Claude Code** del Centro interdipartimentale per l'Umanistica Digitale
(**DH UNICA**) dell'Università degli Studi di Cagliari.

Una skill è una procedura che Claude sa eseguire per conto tuo, con le regole del DH incorporate. Per
esempio: migrare un minisito di progetto nel portale giusto, chiedendoti le scelte importanti e
controllando il risultato. Le skill sono raccolte in **plugin**, uno per area di lavoro.

## Catalogo

| Plugin | Comando | A cosa serve | Livello |
|---|---|---|---|
| `dh-siti` | `/dh-siti:ricognizione-minisito` | Analizza un minisito di progetto e prepara il piano di migrazione | sola lettura |
| `dh-siti` | `/dh-siti:migrazione-minisito` | Migra un minisito di progetto nel portale `{ambito}.dh.unica.it` | produzione |
| `dh-strumenti` | `/dh-strumenti:crea-skill` | Crea una nuova skill secondo lo standard DH | bozze |
| `dh-comunicazione` | `/dh-comunicazione:creazione-slide` | Genera presentazioni nello stile grafico ufficiale DH UNICA | bozze |
| `dh-dati` | `/dh-dati:pubblicazione-dataset` | Trasforma un dataset di ricerca umanistica in un'app statica esplorabile per GitHub Pages e WordPress | bozze |
<!-- fine-catalogo -->

**Livello** indica cosa può modificare la skill:
- *sola lettura*: non cambia nulla;
- *bozze*: crea file o contenuti non pubblicati;
- *produzione*: pubblica su servizi reali, sempre dopo la tua conferma e con un modo per tornare indietro.

Ogni plugin ha un README con le stesse sezioni: cosa fa, quando usarla, prerequisiti, domande che ti
farà, cosa modifica, come tornare indietro, sicurezza, limiti.

## Installazione

In Claude Code:

```
/plugin marketplace add Dh-unica/dh-unica-skill
/plugin install dh-siti@dh-unica-skill
/plugin install dh-strumenti@dh-unica-skill
```

oppure dal terminale:

```bash
claude plugin marketplace add Dh-unica/dh-unica-skill
claude plugin install dh-siti@dh-unica-skill
```

- **Aggiornamenti:** `/plugin marketplace update dh-unica-skill`, oppure attiva l'aggiornamento
  automatico in `/plugin › Marketplaces`. Un plugin si aggiorna quando cambia la sua versione.
- **Repository privato:** serve l'accesso a GitHub dalla riga di comando
  (`gh auth login`, poi `gh auth setup-git`).
- **Rimozione:** `claude plugin uninstall <plugin>@dh-unica-skill`.

### Preconfigurare il marketplace in un progetto

Nei repository dei progetti DH si può aggiungere a `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "dh-unica-skill": {
      "source": { "source": "github", "repo": "Dh-unica/dh-unica-skill" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "dh-siti@dh-unica-skill": true
  }
}
```

Chi apre il progetto e accetta la richiesta di fiducia della cartella trova il marketplace già
registrato. Deve comunque installare il plugin una volta: `claude plugin install dh-siti@dh-unica-skill`.

## Contribuire

Le regole comuni (nomi, struttura, README, versioni, sicurezza, git) sono in
[CONTRIBUTING.md](CONTRIBUTING.md). Il modo più semplice per rispettarle è la skill
`/dh-strumenti:crea-skill`. Prima di ogni merge:

```bash
python3 plugins/dh-strumenti/skills/crea-skill/scripts/check_skills.py .
claude plugin validate . --strict
```

Gli stessi controlli girano in automatico su GitHub (`.github/workflows/validate.yml`).

## Struttura

```
.claude-plugin/marketplace.json     elenco dei plugin
plugins/<dh-area>/
  .claude-plugin/plugin.json        nome, versione, descrizione
  README.md                         documentazione standard per le persone
  CHANGELOG.md                      storia delle versioni
  scripts/                          codice condiviso tra le skill del plugin (facoltativo)
  skills/<azione-oggetto>/
    SKILL.md                        istruzioni per Claude
    references/ assets/ scripts/    materiali della skill (facoltativi)
tests/                              test dei controlli del marketplace
```

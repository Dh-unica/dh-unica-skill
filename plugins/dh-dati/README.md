# dh-dati

> Dati di ricerca del DH: dalla fonte (PDF/OCR, fogli, archivi, Zenodo) a esperienze esplorabili
> pubblicabili su GitHub Pages e nei portali WordPress del DH.

| Skill | Comando | Livello |
|---|---|---|
| `pubblicazione-dataset` | `/dh-dati:pubblicazione-dataset` | bozze |

## Cosa fa

Trasforma una raccolta di dati o documenti di ricerca in un'applicazione web statica: galleria, mappa,
linea del tempo, edizione consultabile. La si apre con un doppio clic, si pubblica su GitHub Pages e si
incorpora in una pagina WordPress. Prima di costruire studia la fonte: cos'è davvero, chi la userà, cosa
nasconde. Poi fa controllare il progetto da un revisore critico, perché il risultato non sia banale.

## Quando usarla

**Sì:** «voglio mettere online le schede delle torri costiere», «facciamo una mappa dei luoghi del
fondo X», «i PDF dell'Almanacco su Zenodo: come li rendiamo esplorabili?», «mi serve un iframe per la
pagina WordPress del progetto».

**No:** pubblicare direttamente su WordPress o depositare su Zenodo (la skill prepara i file, la
pubblicazione la fai tu); basi dati con aggiornamenti continui e utenti autenticati.

## Installazione

```
/plugin marketplace add Dh-unica/dh-unica-skill
/plugin install dh-dati@dh-unica-skill
```

Aggiornamento: `/plugin marketplace update dh-unica-skill` (o aggiornamento automatico da `/plugin`).

## Prerequisiti

- `python3` (bastano le librerie standard).
- Per i PDF: `poppler-utils` (`pdftotext`, `pdfinfo`).
- Per la verifica finale: un browser headless (Chromium o Playwright).
- Nessun account: i record Zenodo pubblici si scaricano senza credenziali.

## Come si avvia

Scrivi a Claude, per esempio:

> Ho il CSV delle torri costiere con coordinate e date: voglio pubblicarlo sul sito del DH

oppure usa il comando `/dh-dati:pubblicazione-dataset`.

## Domande che ti farà

1. Dove sono i dati e qual è la versione canonica da citare.
2. Cartella di lavoro e nome del progetto.
3. Licenza e titolare dei dati, se non risultano dai metadati.
4. Dove finirà: solo GitHub Pages o anche WordPress.
5. **Punto di decisione 1:** livello di lavoro (vetrina, esplorazione, edizione di ricerca).
6. **Punto di decisione 2:** figure di utenti, domande concrete e funzioni da costruire.
7. **Punto di decisione 3:** cosa cambiare dopo la revisione critica, prima di costruire.

## Cosa modifica

**Livello:** bozze

Crea solo file locali nella cartella di lavoro:
- schede di analisi;
- dati normalizzati con manifest delle fonti;
- l'app statica;
- i due blocchi HTML per WordPress.

Non fa push, non scrive su WordPress e non deposita su Zenodo.

## Come tornare indietro

Non serve: basta cancellare la cartella di lavoro.

## Sicurezza e dati personali

Le fonti storiche contengono spesso persone, anche viventi: nomi, nascite, residenze, recapiti. La skill
segue `references/privacy.md` dalla prima fase e controlla l'app finale con `controlla_privacy.py`
(recapiti, date di nascita, codici fiscali). Le versioni canoniche dei dati (Zenodo, DOI) si citano,
non si duplicano.

## Limiti noti

- Al livello *edizione di ricerca* il lavoro richiede settimane: la skill imposta metodo e pilota, non
  sostituisce la ricerca.
- Le estrazioni automatiche (entità, geocodifica) vanno misurate su un campione: la precisione dichiarata
  vale per quel campione.
- L'app è statica: niente aggiornamenti dagli utenti né aree riservate.

## Manutenzione

- **Manutentore:** Alessandro Capra (@caprowsky)
- **Versione:** vedi `.claude-plugin/plugin.json` e [CHANGELOG](CHANGELOG.md)
- **Origine e valutazioni:** progetto `Dh-unica/almanaccostampasarda-analisi` (cartella `skills/`)
- **Segnalazioni:** issue su GitHub con l'etichetta `dh-dati`

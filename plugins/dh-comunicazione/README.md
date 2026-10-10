# dh-comunicazione

> Comunicazione del DH: materiali nello stile grafico ufficiale DH UNICA, a partire dalle presentazioni.

| Skill | Comando | Livello |
|---|---|---|
| `creazione-slide` | `/dh-comunicazione:creazione-slide` | bozze |

## Cosa fa

Crea presentazioni con l'identità visiva del DH UNICA: palette blu, titoli Lora con barra verticale,
Titillium Web, logo DH. Parte da un tema, da materiali o da una presentazione esistente (.pptx o .pdf)
da rifare in stile DH. Consegna una presentazione HTML da proiettare, oppure Markdown (Marp) o PDF.

## Quando usarla

**Sì:** «prepara le slide DH per il seminario di giovedì», «rifai questa presentazione .pptx in stile
DH UNICA», «fammi un deck sul progetto X per la riunione del Centro».

**No:** presentazioni di altri enti o con altri marchi; documenti che non sono slide (relazioni,
locandine).

## Installazione

```
/plugin marketplace add Dh-unica/dh-unica-skill
/plugin install dh-comunicazione@dh-unica-skill
```

Aggiornamento: `/plugin marketplace update dh-unica-skill` (o aggiornamento automatico da `/plugin`).

## Prerequisiti

- `python3` con PyYAML (`pip install pyyaml`) per i deck in YAML.
- Per il PDF: Google Chrome/Chromium (da HTML) oppure `marp` (da Markdown).
- Per ricreare un PDF esistente: `poppler-utils` (`pdftoppm`).

Non servono account né credenziali.

## Come si avvia

Scrivi a Claude, per esempio:

> Prepara 10 slide in stile DH UNICA sul progetto DOG per il convegno di novembre

oppure usa il comando `/dh-comunicazione:creazione-slide`.

## Domande che ti farà

1. Punto di partenza: tema, materiali o presentazione esistente da ricreare.
2. Formato di uscita: HTML (consigliato), Marp o PDF.
3. Occasione e durata: pubblico e numero indicativo di slide.
4. Copertina e chiusura: titolo, autori con ruolo, contatti e sito.

## Cosa modifica

**Livello:** bozze

Crea solo file locali nella cartella che indichi: il deck (YAML), la presentazione (HTML/Markdown/PDF) e
una cartella `assets/` con stili e loghi. Non pubblica nulla.

## Come tornare indietro

Non serve: basta cancellare i file generati.

## Sicurezza e dati personali

Nessuna credenziale. Le slide possono contenere nomi, ruoli e contatti degli autori: inserisci solo
quelli che si possono mostrare in pubblico. I loghi DH UNICA sono un marchio del Centro, esclusi dalla
licenza MIT del repository: si usano solo per materiali del DH.

## Limiti noti

- Solo i 9 layout del catalogo: contenuti molto diversi vanno spezzati o adattati.
- Dai PDF non si estraggono le immagini incorporate: servono gli originali o i ritagli delle pagine.
- I font arrivano da Google Fonts: senza connessione la resa usa font di sistema.

## Manutenzione

- **Manutentore:** Alessandro Capra (@caprowsky)
- **Versione:** vedi `.claude-plugin/plugin.json` e [CHANGELOG](CHANGELOG.md)
- **Segnalazioni:** issue su GitHub con l'etichetta `dh-comunicazione`

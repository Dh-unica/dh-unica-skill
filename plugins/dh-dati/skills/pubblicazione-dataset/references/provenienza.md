# Provenienza, attestazioni, ID e citazione

## Perché
Uno studioso non si fida di un dato di cui non può vedere l'origine. Un curioso, se scopre un errore senza poterne capire la causa, perde fiducia in tutto il sito. La provenienza serve a entrambi, e costa poco se la si prevede fin dall'inizio.

## ID stabili
- Ogni entità (torre, persona, documento, numero) ha un ID che **non cambia** se si aggiungono o tolgono righe.
- Uno schema leggibile aiuta: prefisso di tipo + progressivo o slug, per esempio `TS012`, `PER-cardia-umberto`, `ALM-1968`.
- **Mai l'indice di riga** del foglio. La formula `"TS"&TEXT(ROW()-1,"000")` rinumera tutto se si inserisce una riga in mezzo, e ogni permalink e citazione già pubblicati si rompe. Proponi una colonna `id` compilata una volta e poi congelata. Una formula può suggerire il prossimo ID libero, ma il valore va incollato come testo.

## Attestazioni (modello factoid)
Invece di "la torre X è del 1595", registra "la fonte S, a pagina P, dice che la torre X è del 1595". Campi minimi di un'attestazione:

| campo | esempio |
|---|---|
| `soggetto` | `TS012` |
| `proprieta` | `data_costruzione` |
| `valore` | `1595` |
| `fonte` | `Wikidata Q3995123` / `Montaldo 1992, p. 45` / `DOI:10.5281/zenodo.123 p. 79` |
| `metodo` | `manuale` / `regola` / `calcolo` / `automatico` |
| `confidenza` | `0.9` (solo se il metodo non è manuale) |
| `nota` | facoltativa |

Quando due attestazioni discordano, **mostrale entrambe** nella scheda e segnalale. Non scegliere tu.

Le relazioni (torre ↔ salina, persona ↔ carica) sono attestazioni anch'esse. Il campo `metodo` dice se la relazione è documentata o calcolata, e per quelle calcolate va scritto il parametro usato (per esempio "distanza < 8 km").

## Nel foglio Google dell'autore
Non serve riprogettare il foglio. Bastano tre colonne in più nelle schede master:
- `id` (stabile);
- `fonte_dato`, cioè da dove viene la riga;
- `metodo`.

Per i campi critici (date, coordinate) si può aggiungere `fonte_<campo>`. La scheda `export_*` le porta nei CSV.

## Citazione
Ogni vista elemento ha un permalink e un pulsante "Cita", che produce un testo del tipo:

> Autore/Progetto, *Titolo del dataset*, versione X (anno), elemento `TS012`, <permalink>, DOI.

Se esiste un deposito Zenodo, il DOI è quello del dataset; il permalink identifica l'elemento. Indica sempre la **versione del dataset** (data o numero): i dati cambiano.

## Manifest
`dati/manifest.json` elenca le fonti con: nome, URL o DOI, data di estrazione, licenza, numero di righe, script o query usati. È la base della vista "Fonte e metodo".

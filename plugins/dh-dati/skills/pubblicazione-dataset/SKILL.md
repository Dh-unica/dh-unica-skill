---
name: pubblicazione-dataset
description: >-
  Trasforma un dataset di ricerca storica o umanistica (PDF digitalizzati e OCR, fogli Google o CSV,
  schede d'archivio, dati geografici, elenchi di persone, immagini con metadati, record Zenodo) in
  un'applicazione HTML statica pronta per GitHub Pages, più il blocco da incollare in WordPress. Prima
  di costruire capisce che fonte è, a chi serve e cosa la rende speciale, e verifica che il risultato
  non sia banale. Non scrive su WordPress: produce file statici che l'autore incolla da sé.
when_to_use: >-
  Sempre quando qualcuno del DH UNICA (o un umanista digitale) ha un insieme di dati, documenti o una
  collezione e vuole "pubblicarli sul sito", "metterli online", "farne una mappa o una galleria",
  "renderli consultabili o esplorabili", "fare un'app per il WordPress" o incollare un iframe in una
  pagina, anche se non nomina la skill e chiede solo "una galleria" o "una mappa"; oppure invoca
  /dh-dati:pubblicazione-dataset. Non per pubblicare direttamente su WordPress o Zenodo.
argument-hint: "[cartella o URL dei dati]"
---

# Pubblicare un dataset di ricerca come esperienza esplorabile

Il tuo compito non è "fare una galleria" o "fare una mappa". È trovare **cosa rende interessante questa fonte** e costruire l'interfaccia più semplice che permetta a due persone diverse, un curioso e uno studioso, di scoprirlo e di verificarlo.

Questa skill nasce da un caso reale. L'*Almanacco della Sardegna* era stato pubblicato come 40 copertine con un filtro per decennio. Studiandolo si è visto che metà del corpus era un **annuario seriale della professione giornalistica** (albi, cariche, testate per 45 anni): una fonte prosopografica che la galleria nascondeva del tutto. Il lavoro tecnico era fatto bene (Zenodo, DOI, OCR). È mancato il metodo: chiedersi che fonte fosse, chi l'avrebbe usata e con quali domande. Questa skill serve a non saltare quel passaggio.

L'utente tipico è uno storico digitale esperto che sa già costruire app statiche (GitHub Pages, Google Sheets come CMS, iframe in WordPress). **Rispetta il suo stack.** Non proporre framework, backend o build complessi. Rendi più solido e più profondo quello che fa già.

## Regole (non negoziabili)

1. **Si chiede, non si indovina**: ai tre punti di decisione e nelle domande all'avvio usa
   `AskUserQuestion` con un'opzione «(Consigliata)». Senza un utente che risponde, scegli la consigliata
   e registrala in `DECISIONI.md`.
2. **Non pubblicare nulla**: niente push, niente WordPress, niente Zenodo. L'autore decide quando e dove.
3. **Persone vive**: se nei dati ci sono, `references/privacy.md` viene prima di tutto il resto.
4. **Rispetta lo stack dell'autore** (app statiche, Google Sheets come CMS, iframe in WordPress).
5. I percorsi `scripts/`, `references/`, `templates/` e `agents/` citati sotto sono relativi alla
   cartella della skill: `${CLAUDE_SKILL_DIR}`. Lancia gli script con
   `python3 -I ${CLAUDE_SKILL_DIR}/scripts/<script>.py`.

## Domande all'avvio

1. **Dove sono i dati** (cartella, foglio Google, record o community Zenodo) e qual è la versione
   canonica da citare.
2. **Cartella di lavoro** (predefinita `pubblicazione/<slug-progetto>/`) e slug del progetto.
3. **Licenza e titolare** dei dati, se non risultano dai metadati.
4. **Dove finirà**: solo GitHub Pages, oppure anche una pagina WordPress (quale portale DH).

## Il risultato

Alla fine, nella cartella di lavoro indicata dall'utente (predefinita `pubblicazione/<slug-progetto>/`):

```
<slug>/
├── 00-scheda-fonte.md        cos'è davvero la fonte, strati, serialità, valore nascosto
├── 01-domande-e-persone.md   chi la userà e con quali domande concrete
├── 02-modello-dati.md        entità, relazioni, ID stabili, provenienza
├── 03-revisione-critica.md   esito del controllo "è banale?" e cosa è cambiato dopo
├── DECISIONI.md              ogni scelta presa, da chi, perché (registro breve)
├── dati/                     dati normalizzati + manifest delle fonti
├── sito/                     app statica: index.html, assets/, data/*.js, README.md
│                             (si apre con doppio clic e funziona su GitHub Pages)
└── wordpress/
    ├── embed.html            iframe + script di altezza, da incollare in un blocco HTML
    └── contenuto.html        testo nativo (introduzione, guida, fonte e metodo)
                              da incollare come blocco HTML: rende il progetto
                              indicizzabile, perché l'iframe non lo è
```

## Il processo

Sette fasi. Ognuna produce un file. Alla fine delle fasi 1, 3 e 6 c'è un **punto di decisione**: presenta all'utente la proposta in breve e chiedigli conferma con lo strumento delle domande, se ce l'hai. Se lavori senza un utente che risponde (esecuzione automatica, subagente), scegli tu l'opzione consigliata, scrivila in `DECISIONI.md` con il motivo e vai avanti. Una decisione presa in silenzio è il modo più facile per tradire l'intento dell'utente.

### Fase 1: triage e livello

Guarda i dati prima di parlarne. Per tabelle, CSV, XLSX o JSON lancia `scripts/profila_dati.py <file o cartella>`: ti dà colonne, tipi, valori mancanti, duplicati, coordinate valide e formati delle date. Per i PDF usa `scripts/pdf_testo.py`, per i record Zenodo `scripts/zenodo_fetch.py`. Per un'app esistente, leggi il codice e capisci da dove legge i dati.

Poi rispondi a cinque domande:
1. **Che materiale è?** Formato, quantità, qualità (OCR, completezza, coerenza).
2. **Dove sta la versione canonica?** Zenodo/DOI, un foglio Google, un archivio. Va citata e mai duplicata senza motivo: per esempio niente centinaia di MB di PDF dentro un repo git.
3. **Che licenza ha** e chi ne è titolare?
4. **Ci sono persone vive?** Nomi con nascita, residenza, recapiti, salute, opinioni. Se sì, leggi `references/privacy.md` prima di andare avanti.
5. **Quale livello di lavoro merita?** Leggi `references/livelli.md`.

| Livello | Quando | Sforzo indicativo |
|---|---|---|
| **vetrina** | pochi elementi, fonte omogenea, nessuna struttura nascosta | mezza giornata |
| **esplorazione** | centinaia o migliaia di elementi, relazioni, tempo e spazio | 2-5 giorni |
| **edizione di ricerca** | fonte seriale o stratificata, entità da estrarre, uso scientifico | settimane |

Il livello è la decisione più importante. Il rischio non va in una sola direzione: sottovalutare la fonte (l'Almanacco come galleria) è grave quanto trasformare una lista di poster in un progetto di prosopografia.

**Punto di decisione 1:** presenta il livello proposto, motivato, e chiedi conferma.

### Fase 2: scheda della fonte → `00-scheda-fonte.md`

Leggi `references/tipologie-fonte.md` e riconosci a quali tipologie appartiene il materiale. Spesso sono più d'una: il caso più interessante è proprio quando lo sono. Poi scrivi:
- **Strati.** Quali tipi di contenuto convivono (saggi e albi, schede e immagini, punti e relazioni) e come si riconoscono.
- **Serialità e tempo.** Cosa si ripete e come cambia nel tempo: la forma della fonte cambia? Ci sono lacune?
- **Valore nascosto.** Cosa permette di sapere questa fonte che non si vede sfogliandola? Scrivilo come affermazione verificabile, con un esempio reale preso dai dati.
- **Critica della fonte.** Chi l'ha prodotta, per quale scopo, cosa omette, quanto è affidabile.
- **Problemi dei dati** trovati nel triage: duplicati, campi incoerenti, coordinate mancanti, formati misti.

Usa esempi veri presi dai dati, non generici. "La torre di X è a 3,2 km dalla salina di Y" vale più di "ci sono relazioni spaziali".

### Fase 3: domande e persone → `01-domande-e-persone.md`

Definisci **due figure principali**, più al massimo una terza se il caso lo richiede davvero:
- **il curioso**: un cittadino, un familiare, un appassionato di storia locale, un insegnante;
- **lo studioso**: dallo studente al ricercatore esperto.

Per ciascuna scrivi un nome, un contesto in una riga e **3-5 domande concrete che porrebbe a questi dati**, con nomi, luoghi e date veri presi dal dataset. Poi verifica ogni domanda: **i dati permettono di rispondere?** Se no, la domanda va riformulata, oppure va segnato che servono dati in più. Le domande senza risposta sono il difetto più comune delle personas scritte a tavolino.

Da qui deriva una **lista corta di funzioni**: ogni funzione deve servire almeno una domanda, altrimenti si toglie. Distingui:
- fruizione **aumentata** per il curioso: racconto, percorsi, scoperta, "lo sapevi che";
- fruizione **potenziata** per lo studioso: fonte di ogni dato, citazione, confronto, export, metodo.

Conviene che siano le stesse viste a due profondità, con un interruttore, piuttosto che due siti.

**Punto di decisione 2:** presenta le figure, le domande e la lista delle funzioni, e chiedi conferma.

### Fase 4: modello dei dati → `02-modello-dati.md` e `dati/`

Leggi `references/provenienza.md`. I principi sono tre:
- **ID stabili** per ogni entità. Mai l'indice di riga: quello del foglio cambia se si inserisce una riga.
- **Provenienza su ogni dato.** Fonte, pagina o record, metodo (manuale, regola, automatico) e confidenza quando non è certo. Se due fonti dicono cose diverse, **conserva entrambe le versioni** come attestazioni distinte invece di sceglierne una in silenzio: le contraddizioni sono spesso il dato storico più interessante.
- **Relazioni con il loro perché.** Una connessione "visiva" fra due torri deve dire come è stata stabilita: rilievo, calcolo di distanza o di visibilità, fonte d'archivio.

Normalizza i dati in `dati/` (CSV o JSON) e scrivi un `dati/manifest.json` con le fonti, le date di estrazione e le licenze. Se i dati vivono in un foglio Google, **non sostituirlo**: è il CMS dell'autore. Proponi le colonne in più (ID stabile, fonte, metodo) e uno script o una formula di export.

### Fase 5: pilota e misura

Ogni dato che non hai copiato tal quale dalla fonte va controllato. Cosa controllare dipende da come lo hai ottenuto:
- **Estrazione automatica** (entità da testo, classificazione, geocodifica): fallo su un campione e **misura la precisione**. Verifica a mano 20-30 casi e scrivi il risultato con il margine d'errore. Un numero onesto ("circa 85%, su 30 casi") convince uno studioso più di una mappa piena.
- **Dati calcolati con una regola** (distanze, visibilità, sequenze, raggruppamenti): verifica **la regola**. Ricalcola alcuni casi in modo indipendente, poi cerca dove la regola sbaglia (coordinate duplicate, eccezioni geografiche) e dichiarala con i suoi parametri.
- **Numeri di sintesi** (percentuali, conteggi): indica sempre **il denominatore**. Per esempio "37% delle pagine *descritte dagli indici*", non "delle pagine".

Al livello *vetrina* questa fase si riduce a un controllo a campione di 5-10 elementi.

### Fase 6: revisione critica → `03-revisione-critica.md`

Prima di costruire l'interfaccia, sottoponi scheda, domande e modello a un **critico avversariale**. Se puoi lanciare subagenti, avviane uno con le istruzioni di `agents/critico.md`; è meglio, perché un occhio fresco vede ciò che tu dai per scontato. Altrimenti rileggi tu i documenti con quelle istruzioni, come se fossero di un altro.

Il critico classifica ogni funzione come BANALE, SOLIDA o DISTINTIVA (`references/pattern-banali.md`), controlla 5 affermazioni contro i dati, cerca problemi di privacy e propone 3-5 miglioramenti.

Le critiche fondate vanno **recepite nei documenti a cui si riferiscono**. Se il critico smentisce un numero o un'interpretazione delle fasi 2-4, correggi quel documento con una nota breve "rivisto dopo la revisione critica". Un errore lasciato nella scheda della fonte finisce nell'app e nel testo per WordPress. In fondo a `03-revisione-critica.md` scrivi cosa hai cambiato, cosa no e perché.

Al livello *vetrina* basta una rilettura tua con la checklist di `pattern-banali.md`, senza subagente: per una richiesta semplice una revisione completa costa più del valore che aggiunge.

**Punto di decisione 3**, *prima* di cominciare a costruire: presenta le critiche principali e cosa intendi cambiare.

### Fase 7: costruzione → `sito/` e `wordpress/`

Leggi `references/app-statica.md` (convenzioni tecniche) e parti da `templates/`. I requisiti che contano:
- **Si apre con doppio clic** (file://) **e su GitHub Pages**. I dati vanno in `sito/data/*.js` come `window.DATI = {...}`, oppure caricati dal foglio Google pubblicato con un fallback locale, come fa già l'autore.
- **Un permalink per ogni elemento** (`#/torre/TS012`, `#/anno/1968`): così si può citare e condividere.
- **Una vista "Fonte e metodo"** con provenienza, copertura, lacune, precisione e come citare (DOI + elemento).
- **Il tempo e le relazioni**, se la fonte li contiene, vanno resi esplorabili, non solo filtrabili.
- **Accessibilità di base:** contrasto, tastiera, focus, testo alternativo, nessuna informazione affidata solo al colore. **Responsive** fino a 390 px.
- **Niente artefatti remoti** oltre a librerie da CDN affidabili (cdnjs, unpkg, jsdelivr) e tile cartografici con attribuzione.

Poi:
- `wordpress/embed.html`: iframe con lo script che adegua l'altezza (`templates/embed-wordpress.html`);
- `wordpress/contenuto.html`: introduzione, guida in tre passi per il curioso e per lo studioso, fonte e metodo, come citare, crediti e licenze, in HTML semplice da incollare in un blocco "HTML personalizzato" (`templates/contenuto-wordpress.html`).

**Verifica prima di consegnare.** Apri il sito in un browser headless, controlla che non ci siano errori in console, prova 2-3 permalink e una larghezza mobile. Usa un **browser tuo e isolato**, lanciato da uno script Playwright o con Chromium `--headless`. Il browser dei tool MCP può essere condiviso con altri agenti che lavorano in parallelo, e le pagine si mescolano. Lancia `scripts/controlla_privacy.py sito/` se ci sono persone. Scrivi `sito/README.md` con: come aprirlo, come aggiornare i dati, cosa è reale e cosa illustrativo.

## Consegna

Chiudi con un riepilogo breve per l'autore:
- il livello scelto;
- il valore nascosto trovato;
- le funzioni costruite, ciascuna legata alla domanda a cui risponde;
- cosa ha cambiato la revisione critica;
- i limiti dichiarati;
- i passi per pubblicare: push su GitHub Pages, poi incollare `embed.html` e `contenuto.html` in WordPress.

Non pubblicare tu niente: niente push, niente WordPress, niente Zenodo. L'autore decide quando e dove.

## Riferimenti

| File | Quando leggerlo |
|---|---|
| `references/livelli.md` | fase 1, per scegliere e motivare il livello |
| `references/tipologie-fonte.md` | fase 2, per riconoscere strati e valore nascosto |
| `references/provenienza.md` | fase 4, modello a attestazioni, ID, citazione |
| `references/pattern-banali.md` | fasi 3 e 6, cosa evitare e cosa rende distintivo |
| `references/privacy.md` | se ci sono persone vive, già dalla fase 1 |
| `references/app-statica.md` | fase 7, convenzioni tecniche dell'app e dell'embed |
| `agents/critico.md` | fase 6, istruzioni per il revisore avversariale |
| `scripts/profila_dati.py` | fase 1, profilo di CSV, XLSX e JSON |
| `scripts/pdf_testo.py` | fase 1, testo per pagina da PDF con OCR |
| `scripts/zenodo_fetch.py` | fase 1, download da Zenodo con manifest e md5 |
| `scripts/controlla_privacy.py` | fasi 4 e 7, ricerca di recapiti, date di nascita, codici fiscali |

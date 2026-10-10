---
name: creazione-slide
description: >-
  Genera presentazioni nello stile grafico ufficiale DH UNICA (Centro interdipartimentale per
  l'Umanistica Digitale dell'Università di Cagliari, dh.unica.it): palette blu navy, indaco e azzurro,
  titoli serif Lora con barra verticale, font Titillium Web, strip gradient, logo DH. Parte da un tema,
  da materiali o da una presentazione esistente (.pptx/.pdf) da ricreare. Output HTML+CSS (massima
  fedeltà) o Marp (Markdown), con conversione in PDF.
when_to_use: >-
  Quando l'utente chiede slide, un deck o una presentazione "DH UNICA", "stile DH", "Digital
  Humanities Cagliari", vuole trasformare un tema o dei materiali in slide per il DH, o ricreare in
  stile DH una presentazione esistente (.pptx/.pdf); oppure invoca /dh-comunicazione:creazione-slide.
  Non per presentazioni di altri enti o marchi, né per documenti che non sono slide.
argument-hint: "[tema | file .pptx/.pdf | deck.yaml]"
---

# /dh-comunicazione:creazione-slide

Genera presentazioni nello stile grafico ufficiale **DH UNICA** (dh.unica.it). Replica il brand del sito
(tema Italia / Bootstrap Italia) e del deck di riferimento «DOG – Ecosistema per le Digital Humanities».

## Regole (non negoziabili)

1. **Si chiede, non si indovina**: le scelte variabili (sezione «Domande all'avvio») passano da
   `AskUserQuestion`, sempre con un'opzione «(Consigliata)».
2. **Non inventare nuovi layout**: usa solo quelli del catalogo. Se un contenuto non entra bene, spezzalo
   in più slide.
3. **Non cambiare la palette**: navy, indaco e azzurro sono il brand. Override solo con
   `theme.navy/blue/blue_mid/cyan`.
4. **Font**: sempre Lora (display) e Titillium Web (UI), niente altri Google Fonts. Il serif è solo per
   il display (titoli, cover, divider, numeri delle statistiche), mai per body o UI.
5. **Testo sintetico**: nelle card massimo circa 2 righe di heading e 3 di body; nel lead massimo 2 righe.
6. **Logo** sempre automatico: mai chiedere all'utente di caricarlo. I loghi DH UNICA sono un marchio
   del Centro e si usano solo per materiali del DH.
7. **Ricreazione da un deck esistente**: priorità alla **fedeltà del contenuto**; cambia la grafica,
   non i fatti.

## Domande all'avvio

1. **Punto di partenza**: tema da sviluppare, materiali (testi, repository, documenti) o presentazione
   esistente da ricreare (.pptx/.pdf).
2. **Formato di uscita**: HTML (consigliato, massima fedeltà), Marp (Markdown modificabile) o
   PDF finale.
3. **Occasione e durata**: pubblico (convegno, lezione, riunione) e numero indicativo di slide.
4. **Copertina e chiusura**: titolo, autori con ruolo, contatti e sito da mostrare.

## Design system (fisso, non reinventarlo)

- **Navy display**: `#163a6b`, per titoli e numeri, in **serif Lora** bold.
- **Blu indaco**: `#2f4299` (brand dh.unica.it); **blu hero**: `#3980bf`; **azzurro**: `#27a7e5`.
- **Font**: **Lora** (serif) per titoli display, cover, divider e numeri; **Titillium Web** (sans) per
  UI, lead, body, tabelle e badge.
- **Firma grafica**:
  - ogni titolo di sezione ha una **barra verticale blu** a sinistra;
  - in basso una **strip gradient** navy → blu → cyan;
  - un glow azzurro tenue in alto a destra.
- **Logo**: marchio DH «DigitalHumanities · UniversitàDiCagliari», nero in alto a destra nelle slide
  interne, bianco nella closing.
- **Pannelli contenuto**: grigio chiaro `#eef1f5` con bordo inferiore navy.
- **Card**: accent-bar superiore che ruota sui 6 colori delle icone della home (rosso, blu, verde,
  magenta, teal, arancio).

## Catalogo layout (usa solo questi)

| id | uso |
|---|---|
| `cover` | copertina: titolo serif + sottotitolo + autori/contatti + logo |
| `section-divider` | separatore di sezione: barra verticale + grande titolo serif |
| `lead-bullets` | titolo + paragrafo lead + pannello con elenco puntato (immagine opzionale a destra) |
| `cards` | titolo + lead + griglia di card (kicker/icona + heading + body), 2/3/4 colonne |
| `tech-list` | titolo + lead + elenco verticale con badge + nome + descrizione (immagine opzionale) |
| `table` | titolo + tabella con header navy e righe alternate |
| `stats-row` | titolo + numeri grandi serif + pannello descrizione opzionale |
| `image-showcase` | titolo + grande immagine/screenshot in cornice |
| `closing` | chiusura su fondo navy: titolo serif (es. «Domande?») + sottotitolo + crediti + sito |

### Scelta dei layout

- Prima slide → `cover`; ultima → `closing`.
- Cambio capitolo, o slide con solo un titolo → `section-divider`.
- Testo introduttivo + elenco puntato → `lead-bullets`.
- Da 3 a 6 concetti paralleli → `cards`.
- Stack tecnologico o elenco di strumenti con etichetta → `tech-list`.
- Dati tabellari → `table`.
- Metriche o numeri chiave → `stats-row`.
- Slide dominata da un'immagine o uno screenshot → `image-showcase`.

## Procedura

Serve `python3` con PyYAML (`pip install pyyaml`) per i deck in YAML; i JSON non hanno dipendenze.

### Caso A: tema, istruzioni o materiali

1. Se l'utente fornisce un file YAML/JSON strutturato, passa direttamente al rendering.
2. Altrimenti costruisci tu un deck YAML scegliendo i layout dal catalogo (mai inventarne altri),
   salvalo nella cartella di lavoro dell'utente e procedi al rendering. Schema in
   `${CLAUDE_SKILL_DIR}/schema/deck.schema.json`. L'esempio completo è la ricostruzione del deck DOG
   in `${CLAUDE_SKILL_DIR}/examples/example-deck.yaml`.

### Caso B: ricreare una presentazione esistente (.pptx / .pdf)

Va **preservato il contenuto**, con modifiche minime: cambia solo la grafica.

1. Estrai contenuto **e immagini**:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/extract.py <input.pptx> <lavoro>/src.json --media <lavoro>/assets/img
   ```
   - Dal `.pptx` estrae testi, **tabelle** e **immagini incorporate**. Ogni slide nel JSON ha una lista
     `images` con `file`, `bytes`, `used_in_slides`, `decorative`.
   - Le immagini con `decorative: true` (loghi, decori ricorrenti, icone sotto 8 KB) vanno **ignorate**.
     Come contenuto si usano solo quelle con `decorative: false`.
   - Per i `.pdf` `--media` non è disponibile, perché le immagini sono fuse nella pagina. Estrai le
     pagine con `pdftoppm -png input.pdf page` e ritagliale, oppure chiedi all'utente i file originali.
2. Mappa **ogni slide** sul layout più adatto del catalogo, conservando testi, elenchi, tabelle, numeri
   **e le immagini di contenuto** (campo `image:` nei layout `lead-bullets`, `tech-list`,
   `image-showcase`). Riscrivi solo per chiarezza o sintesi, senza alterare il significato.
3. Mantieni l'ordine originale delle slide; usa `cover` per la prima e `closing` per l'ultima.
4. Se una slide dell'originale era **volutamente vuota** (es. un divider che precede una demo dal
   vivo), riproducila come `section-divider` invece di inventare contenuto.

### Rendering

```bash
# HTML (default, massima fedeltà)
python3 ${CLAUDE_SKILL_DIR}/render.py <deck.yaml> [output.html]
# Marp (Markdown)
python3 ${CLAUDE_SKILL_DIR}/render.py <deck.yaml> --marp [output.md]
```

Il renderer copia in automatico CSS e loghi nella cartella `assets/` accanto all'output.
Design tokens in `${CLAUDE_SKILL_DIR}/templates/html/styles.css`; tema Marp in
`${CLAUDE_SKILL_DIR}/templates/marp/theme.css`.

PDF finale:

```bash
# HTML → PDF 16:9 con Chrome headless
google-chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=deck.pdf deck.html
# Marp → PDF
marp deck.md --theme dh-unica-theme.css --pdf --allow-local-files
```

### Verifica

Apri l'HTML nel browser: scala in automatico al viewport, si naviga con frecce o spazio, `F` attiva il
fullscreen. Per controllare la resa, converti in PDF e ispeziona le pagine.

## Output per l'utente

Percorso dei file prodotti (HTML/Marp/PDF), numero di slide e layout usati, eventuali contenuti
rimasti fuori o spezzati in più slide, e come modificarli (file YAML del deck).

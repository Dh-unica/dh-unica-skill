---
name: migrazione-minisito
description: >-
  Migra un piccolo sito di progetto (per lo più statico, WordPress+Elementor o HTML) dentro un
  portale del Centro DH UniCA alla URL {ambito}.dh.unica.it/{progetto}/ secondo la name convention
  DH. Procedura completa e collaudata: ricognizione, domande all'utente, piano, conversione in
  blocchi Gutenberg, caricamento in bozza via REST, verifica automatica, pubblicazione, voce nel
  menu Progetti, barra di sezione del progetto, redirect 301.
when_to_use: >-
  Quando l'utente chiede di migrare, portare o ricondurre un minisito di progetto dentro
  storia/musica/cinema/archivistica/geografia.dh.unica.it, di dismettere il dominio di un progetto
  portandolo nel portale DH, o invoca /dh-siti:migrazione-minisito. Non per creare contenuti nuovi, per
  siti grandi con blog o e-commerce, o per modificare pagine già esistenti del portale.
argument-hint: "[url-minisito] [ambito]"
---

# /dh-siti:migrazione-minisito: minisiti di progetto → portali DH UniCA

Procedura messa a punto e collaudata migrando `laricchezzadellachiesa.com` in
`storia.dh.unica.it/laricchezzadellachiesa/` (12 pagine, 30 media, verifica 12/12, ottobre 2026).
Lo strumento è il pacchetto Python `dhmigrate`, incluso nel plugin in `${CLAUDE_PLUGIN_ROOT}/scripts/`
(condiviso con la skill `ricognizione-minisito`).

## Principi (non negoziabili)

1. **Name convention DH**: `https://{ambito}.dh.unica.it/{progetto}/…`. Lo slug di progetto è tutto
   minuscolo, senza separatori né accenti; il progetto è una pagina radice e tutte le pagine sono sue
   discendenti. `geo` e `xdams` sono sottodomini API e non ospitano minisiti.
   Dettagli: `references/name-convention.md`.
2. **Mai sovrascrivere ciò che non è nostro.** Lo strumento modifica solo pagine, media e voci di menu
   registrati in `state.json`; se trova uno slug già occupato si ferma (ConflictError). Widget e
   impostazioni del portale non si toccano.
3. **Navigazione su due livelli, mai pulsanti in pagina.**
   - *Menu globale del portale*: il progetto è una voce sotto «Progetti» e le voci del menu sorgente ne
     sono il sottomenu (`Progetti › La ricchezza della Chiesa › Il Progetto, Equipe, …`). «Home» non si
     replica: è la voce del progetto stessa.
   - *Barra di sezione del progetto* in testa a ogni pagina: percorso `Progetti › <progetto>` e menu del
     progetto con la voce corrente evidenziata. È un pattern sincronizzato con un blocco Navigation:
     si modifica una volta e vale per tutte le pagine.
   Serve perché il menu globale mostra le sottovoci solo a tendina: senza barra, chi è su «Equipe» non
   capisce in quale progetto si trova (problema emerso sulla prima migrazione). La **posizione
   nell'alberatura va sempre confermata dall'utente** prima di scrivere sul menu.
4. **Ogni scelta variabile si chiede all'umano** (sezione «Domande all'avvio»). Proponi un default
   motivato, ma non decidere al posto dell'utente.
5. **Bozza → verifica → pubblicazione.** La pubblicazione è un comando separato (`publish --yes`) e su
   un sito di produzione va confermata dall'utente, salvo autorizzazione esplicita già data.
6. **Credenziali fuori dal repo**: `~/.config/dh-unica/wp-<ambito>.env` con permessi 600
   (`WP_USER`, `WP_APP_PASSWORD`). Mai in chiaro in documenti, commit o messaggi.
7. **Git: un branch per task** (`docs/…`, `feat/…`, `fix/…`, `chore/run-<progetto>`), commit
   convenzionali e merge `--no-ff` (o PR con `gh` se c'è un remote). Mai commit diretti su `main`.

## Prerequisiti

```bash
# una tantum: virtualenv fuori dalla cartella del plugin (che si aggiorna)
${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh ${CLAUDE_PLUGIN_DATA}/venv
DHM="env PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/scripts ${CLAUDE_PLUGIN_DATA}/venv/bin/python -m dhmigrate"
```

Le variabili di shell non sopravvivono tra un comando e l'altro: ripeti la definizione di `DHM`
all'inizio di ogni comando che lo usa.

**Credenziali (Application Password).** La password **non deve mai passare nella chat**.
1. L'utente la crea nel portale: *Bacheca › Utenti › Profilo › Password applicazione*, con un nome
   riconoscibile (es. `dhmigrate-<cognome>-<progetto>`). Serve un utente **amministratore del sito**,
   perché i menu richiedono `edit_theme_options`; per sole pagine e media basta un Editor.
2. La salva **lui stesso**, nel proprio terminale. In Claude Code basta il prefisso `!`: il comando
   gira nella shell dell'utente e Claude non vede la password:
   ```bash
   ! env PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/scripts ${CLAUDE_PLUGIN_DATA}/venv/bin/python -m dhmigrate login --url https://<ambito>.dh.unica.it
   ```
   Il comando chiede utente e password (nascosta), li verifica con l'API e li scrive in
   `~/.config/dh-unica/wp-<ambito>.env` con permessi 600. Avvisa se l'utente non può modificare i menu.
3. Su server o CI si usano le variabili d'ambiente `DHM_WP_USER` e `DHM_WP_APP_PASSWORD`, che hanno
   la precedenza sul file.
4. A migrazione chiusa, suggerisci di **revocare** la password dal profilo WordPress.

Se l'utente incolla comunque la password in chat, non ripeterla, salvala con lo stesso formato
(file 600) e suggerisci di revocarla a fine lavoro.

## Domande all'avvio (obbligatorie)

Appena invocata la skill, raccogli le risposte con `AskUserQuestion` (al massimo 4 domande per
chiamata, raggruppate per tema). Proponi sempre un'opzione «(Consigliata)» ricavata dai dati,
mai una risposta data per scontata. Se una risposta è già nella richiesta dell'utente, non
richiederla, ma riportala nel riepilogo.

**Prima della ricognizione:**
1. **URL del minisito sorgente**.
2. **Ambito DH** (sottodominio): proponi quello della disciplina del progetto
   (`references/name-convention.md`).
3. **Slug di progetto**: proponi `suggest_slug(nome progetto)` e mostra la URL finale
   `https://{ambito}.dh.unica.it/{slug}/`.
4. **Credenziali**: chiedi se la Application Password è già salvata con `dhmigrate login`. Se non lo è,
   guida l'utente come spiegato in «Prerequisiti», senza farti incollare la password.

**Dopo la ricognizione** (servono i dati di `survey.md`):
5. **Posizione nel menu globale**: mostra l'albero del menu del portale (`survey.md`, sezione «Menu
   del portale») e proponi «sotto *Progetti*, dopo l'ultimo progetto». Chiedi conferma della voce
   genitore e dell'**etichetta** della voce del progetto (es. «La ricchezza della Chiesa»).
6. **Sottovoci del progetto**: proponi le voci del menu sorgente, Home esclusa. Chiedi se aggiungerne o
   toglierne e se rinominarle. Le stesse voci compaiono nel menu globale e nella barra di sezione.
7. **Testata del progetto**: proponi la testata propria (consigliata): sulle pagine del progetto titolo,
   menu e `<title>` sono quelli del progetto e il ritorno al portale sta nella barra alta, come in
   «Colonizzazioni interne». Chiedi sottotitolo, immagine di banner (di solito l'immagine di copertina
   del sito sorgente) e link della barra alta (default `Storia Digitale UniCA` e `DH UniCA`). Il
   percorso della barra di sezione (default `Progetti`) resta come ripiego per chi non ha JavaScript.
   Senza testata, il progetto si naviga dal menu globale più la barra in pagina: è il caso che i PI
   hanno trovato confuso («un sito dentro un sito»).
8. **Albero delle URL e rinomine**: mostra l'albero proposto e le rinomine consigliate (es. slug
   inglesi o generici come `about` → `progetto`).
9. **Titolo della pagina radice** (nome esteso del progetto).
10. **Elementi non migrabili 1:1** emersi dalla ricognizione, una domanda per tipo:
   - moduli di contatto: testo sostitutivo oppure modulo Contact Form 7 (e destinatario);
   - loghi del footer: blocco «Partner e finanziatori» sì o no;
   - articoli o blog: escludere, aggregare in una pagina o migrare a parte;
   - incongruenze di contenuto: segnalarle al PI senza correggerle.
11. **Pubblicazione**: fermarsi alle bozze, oppure pubblicare (e creare le voci di menu) dopo la verifica.

Riporta le risposte nel piano (sezione 5, «Albero e menu») e nella config.

## Procedura

Usa una cartella di lavoro di progetto: un repo git con `docs/`, `config/`, `runs/`, `work/` (ignorata).

### 1. Ricognizione (sola lettura)

```bash
$DHM survey --source https://<minisito> --slug <progetto> --ambito <ambito> \
            --workdir work
```

Produce due file:
- `work/<progetto>/survey.md`: piattaforma, builder, pagine, widget, menu sorgente, **albero del menu
  del portale**, destinazione, permessi, conflitti;
- `config.proposta.yaml`.

Nell'albero proposto le voci di menu stanno sotto la radice; le pagine fuori menu finiscono sotto la
pagina di menu che le linka.

Poi fai le domande 5-11 di «Domande all'avvio» e aggiorna la config con le risposte.

### 2. Piano (documento)

Branch `docs/piano-migrazione`. Scrivi `docs/piano-migrazione-<progetto>.md` partendo da
`assets/piano-template.md`. Compila tutte le sezioni con i dati reali della ricognizione: è il
documento che spiega a colleghi e PI cosa succederà. Commit e merge.

### 3. Config

Copia `config.proposta.yaml` in `config/<progetto>.yaml` e rifinisci; un esempio completo e collaudato
è in `assets/config-esempio.yaml`. Campi utili:
- `pages[].title`: titolo in destinazione (per la radice, il nome esteso del progetto);
- `menu`: posizione **confermata dall'utente** nel menu globale: `location` (es. `menu-main`), `parent`
  (titolo della voce genitore, es. `Progetti`), `label` (etichetta della voce del progetto). Se l'utente
  non vuole toccare il menu, ometti la sezione;
- `pages[].menu_label`: la pagina diventa una sottovoce del progetto nel menu globale e nella barra di
  sezione (ordine = ordine in config);
- `section_nav.breadcrumb`: voci del percorso prima del progetto (es. `[{label: Progetti, url: …}]`);
  ometti la sezione per non creare la barra;
- `section_nav.header`: testata propria del progetto: `title` (default `project.title`), `subtitle`,
  `banner` (URL sorgente dell'immagine, caricata tra i media) e `links` (barra alta, ritorno al portale).
  La radice entra nel menu del progetto con il suo `menu_label` (es. `Home`);
- `pages[].image_width`: larghezza uniforme delle immagini di contenuto (es. le foto dell'équipe);
- `partners`: loghi del footer sorgente → blocco «Partner e finanziatori» sulla radice;
- `notes.form_replacement`: testo che sostituisce i moduli di contatto non migrabili;
- `source.elementor_default_direction`: `row` o `column` per i container Elementor senza direzione nel
  CSS. Nel dubbio, controlla nel browser con `getComputedStyle(el).flexDirection` sui `.e-con`.

Controllo: `$DHM check --config config/<progetto>.yaml`.

### 4. Extract + Transform (offline)

```bash
$DHM extract   --config config/<progetto>.yaml
$DHM transform --config config/<progetto>.yaml   # blocchi, media e avvisi per pagina
```

Leggi gli avvisi e apri 2-3 file di `work/<progetto>/transform/*.html`. Per un widget convertito «in
modo generico» o una resa scorretta, correggi il convertitore (`dhmigrate/transform.py`, metodo
`w_<widget>`) su un branch `feat/…`/`fix/…` **con un test sulla fixture HTML reale**, poi rilancia.

### 5. Load in bozza + verifica

Branch `chore/run-<progetto>`.

```bash
$DHM load --dry-run --config config/<progetto>.yaml   # preflight: permessi, conflitti, piano chiamate
$DHM load           --config config/<progetto>.yaml   # media + pagine in BOZZA + barra di sezione
$DHM verify         --config config/<progetto>.yaml   # copertura testo, residui, immagini, link
```

`load` si può rilanciare quante volte serve: aggiorna le pagine esistenti, non ricarica i media già
caricati e rimuove i media nostri non più usati. `verify` deve dare **tutte OK** (copertura ≥ 98%).
I WARN su link esterni con 403/999 (Academia.edu, LinkedIn) vengono dai blocchi anti-bot e non sono errori.

### 6. Pubblicazione e controllo visivo

Su conferma dell'utente:

```bash
$DHM publish --yes --config config/<progetto>.yaml   # pubblica le pagine e crea le voci di menu
$DHM verify        --config config/<progetto>.yaml   # ora controlla anche HTTP 200 e URL pubbliche
```

Le voci di menu si creano solo con le pagine pubblicate, perché WordPress nasconde quelle che puntano a
bozze. Per riallineare solo la navigazione (dopo aver cambiato `menu`, `section_nav` o un `menu_label`):
`$DHM menu --dry-run …`, poi `$DHM menu --yes …`: aggiorna voci del menu globale, barra di sezione e
testata senza riscrivere le pagine. Le voci vengono inserite subito dopo l'ultimo figlio
della voce genitore; le voci successive scalano in avanti e il loro ordine originale finisce in
`state.json`, così il rollback lo ripristina.

Controlla il menu nel browser: passa il mouse su «Progetti» e poi sulla voce del progetto, e fai uno
screenshot del sottomenu aperto. Con la testata attiva controlla anche, su una pagina del progetto, il
titolo nella testata e nella scheda del browser, la voce corrente evidenziata (anche nelle sottopagine),
il menu mobile (icona ☰) e che una pagina fuori dal progetto mostri ancora la testata del portale.

Screenshot con Playwright MCP, desktop (1366) e mobile (390), di radice, pagina più ricca e Contatti.
**Prima di fotografare scorri tutta la pagina**: immagini e iframe sono in lazy-load e altrimenti
sembrano mancare. Se trovi difetti, correggi su un branch `fix/…`, rilancia `load` (le pagine
pubblicate restano pubblicate) e `verify`.

### 7. Chiusura

```bash
$DHM redirects --config config/<progetto>.yaml --out docs   # csv + .htaccess + nginx per il vecchio dominio
```

Copia in `runs/<progetto>/` i file `state.json`, `verify-report.md` e `transform/report.json` e
alcuni screenshot. Compila la sezione «Esito» del piano: ID pagine, problemi risolti e azioni
residue (redirect sul vecchio hosting, voce nel menu globale, correzioni di contenuto per il PI).
Commit e merge.

**Rollback** (se richiesto): `$DHM rollback --yes --config …` sposta le pagine nel cestino ed elimina i
soli media caricati dalla migrazione; elimina le voci di menu create e ripristina l'ordine di quelle spostate.

## Casi particolari

Leggi `references/casi-particolari.md` quando: la sorgente non è WordPress, ci sono widget non
supportati, moduli, iframe o mappe che spariscono, immagini AVIF/WebP, multisito senza
`unfiltered_html`, pagine multilingua o articoli/blog.

## Output atteso per l'utente

Un messaggio finale breve con: URL della radice migrata, tabella pagine → URL, esito della verifica,
problemi trovati e risolti, azioni residue che spettano a persone (redirect, menu, contenuti) e link al
documento di piano aggiornato.

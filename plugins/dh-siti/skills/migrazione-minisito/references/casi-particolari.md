# Casi particolari e insidie note

Raccolti durante la migrazione di laricchezzadellachiesa.com e durante l'analisi dei portali DH.

## Sorgente

| Situazione | Cosa fare |
|---|---|
| **Sorgente non WordPress** (HTML statico, Wix, Google Sites) | `source.type: static`: il crawler BFS segue i link interni e prende `<main>`/`<article>`/`#content`. Controlla `extract/pages.json` e assegna in config gli slug (derivati dal path). Per i builder SaaS con contenuto generato da JS il crawler vede poco: valuta di salvare le pagine dal browser (Playwright MCP) e metterle in `extract/html/`. |
| **WordPress senza Elementor** (Gutenberg o classico) | `content.rendered` passa da `html_to_blocks`, che produce paragrafi, titoli, liste, immagini, tabelle e citazioni puliti. |
| **Articoli (post), oltre alle pagine** | Lo strumento migra solo le pagine. Per pochi articoli (news, eventi) valuta di aggregarli in una pagina «Notizie» o di estendere `extract` con `/wp/v2/posts` su un branch `feat/…`. |
| **Pagine multilingua senza plugin** (IT + EN come pagine separate) | Tienile come pagine sorelle sotto la stessa sezione (es. `progetto/state-of-art`). Non inventare strutture `/en/`. |
| **Container Elementor senza direzione nel CSS** | Il default dipende dal kit del sito. Controlla nel browser `getComputedStyle(e).flexDirection` sui `.e-con` e imposta `source.elementor_default_direction`. |
| **HTML Elementor malformato** (`<h2>` dentro `<h2>`) | Già gestito: i blocchi annidati vengono separati con un a capo. Se `verify` segnala parole mancanti, cerca nella sorgente il contesto delle parole elencate. |
| **Segnaposto Elementor** (`placeholder.png`) | Già scartato: è un widget immagine vuoto. |
| **Immagini di sfondo** (hero) | Stanno nel CSS `post-<id>.css` e non nell'HTML: `extract` lo scarica, `transform` le rende come blocco `core/cover`. |

## Destinazione

| Situazione | Cosa fare |
|---|---|
| **AVIF/HEIC** | I server datati (es. nginx 1.10) li servono come `application/octet-stream` e, con `nosniff`, il browser non li mostra. `load` li converte in JPEG (Pillow). Se un AVIF è già stato caricato prima della correzione: elimina quel media (solo se `created: true` in state), toglilo da `state.json` e rilancia `load`. |
| **Multisito: utente senza `unfiltered_html`** | Iframe (mappe, embed non oEmbed) e `<script>` vengono filtrati al salvataggio. Il `survey` lo segnala. Alternative: blocco `core/embed` per i provider oEmbed, link testuale alla mappa, oppure caricamento da un super-admin. |
| **Moduli di contatto** (WPForms, CF7, Elementor Form) | Non migrabili: diventano il testo di `notes.form_replacement`. Se serve un modulo, creane uno Contact Form 7 solo dopo aver deciso con il PI il destinatario delle e-mail. |
| **Menu globale del portale** | È il posto della navigazione del minisito: `Progetti › <progetto> › <sottovoci>`, mai pulsanti in pagina. Posizione ed etichette vanno confermate dall'utente. Il tema Design Italia mostra correttamente il terzo livello (sottomenu laterale all'hover), verificato su storia.dh.unica.it. Se la voce genitore non esiste o compare più volte, `menu` si ferma: chiedi all'utente quale usare. |
| **Orientamento nelle sottopagine** | Il menu globale mostra le sottovoci solo a tendina (desktop: hover sul terzo livello; mobile: menu a scomparsa), quindi dentro «Equipe» il visitatore non sa dove si trova. Soluzione standard: barra di sezione (`section_nav`), cioè un pattern sincronizzato con percorso e blocco Navigation (`overlayMenu: never`, voce corrente marcata con `current-menu-item`). Il CSS sta dentro il pattern e richiede `unfiltered_html`: senza, la barra funziona ma senza evidenziazione. |
| **Soluzione strutturale (futura)** | Un child theme di Design Italia che mostra in automatico breadcrumb e menu di sezione per ogni pagina figlia di un progetto renderebbe superflua la barra nel contenuto. Richiede accesso al server del multisito: da proporre ai sistemisti del DH. |
| **Menu con location diverse** | `survey.md` indica la location usata (`menu-main` su Design Italia). Altri temi possono usare `primary` o simili: elenco con `GET /wp/v2/menu-locations`. |
| **Slug radice già occupato** | `load` si ferma. Capisci con l'utente se è una migrazione precedente (allora recupera gli ID e ricostruisci `state.json`) o un contenuto diverso (allora scegli un altro slug). |
| **Tema Design Italia (Bootstrap Italia)** | Rende bene i blocchi core (`columns`, `cover`, `buttons` outline, `embed`). Template `page-fullwidth.php`, come le altre pagine di progetto. |

## Verifica

| Situazione | Cosa fare |
|---|---|
| Screenshot con immagini o mappe «mancanti» | Quasi sempre è il lazy-load. Scorri la pagina via `browser_evaluate` e controlla `img.naturalWidth > 0` e le dimensioni degli iframe prima di concludere che manchino. |
| WARN 403/999 su Academia.edu, LinkedIn | Blocchi anti-bot, non link rotti. |
| Copertura testo < 98% | `verify` elenca le parole mancanti: di solito un widget non gestito o testo dentro attributi. Correggi il convertitore con un test. |
| Incongruenze nei contenuti sorgente (es. `mailto:` diverso dal testo mostrato) | Non correggerle di tua iniziativa: riportale tali e quali e segnalale nel piano tra le azioni per il PI. |

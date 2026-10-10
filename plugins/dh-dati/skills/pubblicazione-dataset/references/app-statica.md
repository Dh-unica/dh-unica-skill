# Convenzioni tecniche dell'app statica

L'obiettivo è un'app che l'autore possa mantenere da solo, con gli strumenti che usa già: HTML, CSS e JS senza build, GitHub Pages, foglio Google come CMS, iframe in WordPress.

## Struttura
```
sito/
├── index.html
├── assets/app.css
├── assets/app.js          router a hash, viste, ricerca
├── data/dati.js           window.DATI = {...}  (generato da dati/ con uno script)
├── img/                   immagini ridotte, se servono
└── README.md
```

## Dati
- **Default: `data/dati.js`.** Funziona da file:// (doppio clic) e su GitHub Pages, senza problemi di CORS. Generalo con un piccolo script Python da `dati/`.
- **Se l'autore aggiorna i dati da un foglio Google** e vuole l'app sempre aggiornata, leggi il CSV pubblicato (`/pub?output=csv` oppure `gviz/tq?tqx=out:csv`) con **fallback** su `data/dati.js`, e mostra all'utente quale fonte è attiva. È il pattern che l'autore usa già.
- **Niente file pesanti nel repo.** I PDF e le immagini ad alta risoluzione stanno su Zenodo; l'app li linka o li carica da lì.
- Oltre qualche MB di dati, dividi per vista (`data/persone.js`, `data/testi.js`) e caricali solo quando servono.

## Navigazione e permalink
- Router a hash: `#/`, `#/elemento/<ID>`, `#/anno/<anno>`, `#/metodo`, `#/cerca?q=...`.
- Ogni vista ha un titolo `<h1>`. Al cambio di vista sposta il focus sul titolo e aggiorna `document.title`.
- I link interni sono `<a href="#/...">` veri, non `div` cliccabili.

## Viste minime
1. **Home**: cosa è, perché è interessante (il valore nascosto in una frase con un esempio), due ingressi (curioso e studioso).
2. **Elemento**: scheda con dati, provenienza, relazioni, permalink e pulsante "Cita".
3. **Esplorazione**: la vista distintiva del progetto (timeline, mappa con relazioni, serie…).
4. **Ricerca**.
5. **Fonte e metodo**: fonti, licenze, copertura, lacune, precisione, versione, come citare, privacy, contatti.

Interruttore "Mostra fonti e dati" per la fruizione potenziata: ID, confidenze, metodo, tabelle ed export CSV/JSON di ciò che si vede.

## Mappe
- Leaflet da unpkg o cdnjs, con tile **e attribuzione visibile**.
- **Tile e file://.** Da una pagina aperta con doppio clic il browser non manda il `Referer`. Molti fornitori allora rifiutano: OpenStreetMap risponde 403 "Access blocked", CARTO «API KEY REQUIRED». Scegli i tile in base al protocollo:
  ```js
  const locale = location.protocol === 'file:';
  const tiles = locale
    ? L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        {attribution: 'Tiles © Esri'})
    : L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {attribution: '© OpenStreetMap contributors'});
  ```
  Prova comunque la mappa in tutti e due i modi: le politiche dei fornitori cambiano.
- Relazioni come linee con stile per tipo, dove documentate e calcolate si distinguono (continua o tratteggiata), con una legenda.
- Un cursore temporale se ci sono periodi; normalizza i periodi in `anno_da`/`anno_a` e conserva la forma originale.

## Grafici
SVG scritto a mano o una libreria leggera da CDN. Ogni grafico ha un titolo, il numero dei casi, una nota sulle discontinuità e `role="img"` con `aria-label`. Non affidare il significato solo al colore.

## Stile
Sobrio, editoriale, leggibile: serif per i testi lunghi, sans per i dati, una palette di 2-3 colori più i neutri. Contrasto AA. Responsive fino a 390 px senza scroll orizzontale. Niente aspetto da template.

## Embed in WordPress
- `wordpress/embed.html`: iframe con `title`, `loading="lazy"` e lo script di `templates/embed-wordpress.html`. L'app comunica l'altezza con `postMessage`, e l'origine va controllata da entrambe le parti.
- `wordpress/contenuto.html`: testo nativo in HTML semplice (h2, p, ul, a), senza script, da incollare in un blocco "HTML personalizzato". Il contenuto dentro l'iframe non viene indicizzato dai motori di ricerca: questo blocco porta su WordPress introduzione, guida, metodo e citazione.
- Nell'app, quando è dentro un iframe, i link "apri a schermo intero" puntano all'URL di GitHub Pages con lo stesso hash.

## Verifica
- Browser headless: zero errori in console, 2-3 permalink, larghezza 390 px.
- `scripts/controlla_privacy.py sito/` se ci sono persone.
- Peso totale: segnalalo nel README se supera i 10 MB.

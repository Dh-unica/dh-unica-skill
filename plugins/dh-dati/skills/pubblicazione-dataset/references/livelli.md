# Scegliere il livello di lavoro

Il livello dice quanto lavoro merita il dataset. Va motivato con evidenze prese dal triage, non a sensazione.

## Vetrina (mezza giornata)

**Quando:** pochi elementi (fino a qualche centinaio), omogenei, senza strati o serie nascoste. Per esempio i poster di un convegno, una raccolta di 40 fotografie con didascalia, un elenco di eventi.

**Cosa si fa:**
- scheda della fonte breve, mezza pagina;
- due figure con 3 domande ciascuna;
- modello minimo: ID, fonte, licenza;
- app con elenco o griglia, scheda dell'elemento con permalink, ricerca, "Fonte e metodo";
- revisione critica rapida, fatta da te, sulla checklist di `pattern-banali.md`.

**Errore tipico:** saltare la scheda della fonte perché "è solo una galleria". È proprio il caso dell'Almanacco: sembrava una galleria.

## Esplorazione (2-5 giorni)

**Quando:** centinaia o migliaia di elementi, oppure relazioni tra entità, una dimensione temporale o spaziale significativa, più tabelle collegate. Per esempio torri e infrastrutture costiere con connessioni, un repertorio di parlamentari, una rete di corrispondenze.

**Cosa si fa:**
- tutte le fasi;
- un pilota se c'è un'estrazione o un calcolo, come distanze, visibilità o geocodifica;
- viste su relazioni e tempo;
- revisione critica fatta da un subagente.

**Errore tipico:** la mappa a puntini con il popup. La mappa è il punto di partenza, non il risultato: la domanda è cosa si capisce *mettendo in relazione* i punti.

## Edizione di ricerca (settimane)

**Quando:** la fonte è seriale o stratificata (periodici, annuari, registri, catasti, verbali), ci sono entità da estrarre dal testo, l'uso previsto è scientifico. Per esempio l'Almanacco della Sardegna (41 numeri, albi professionali, 45 anni), una serie di verbali consiliari, un catasto storico.

**Cosa si fa:**
- tutte le fasi in profondità;
- estrazione con misura della precisione per periodo;
- modello ad attestazioni, con le contraddizioni conservate;
- più cicli di revisione critica;
- un mockup prima dell'app definitiva.

**Errore tipico:** promettere serie e carriere senza misurare quanto è affidabile l'estrazione per ogni periodo della fonte.

## Segnali che il livello è da alzare

- La fonte **cambia forma nel tempo**: una rivista che diventa annuario, un registro che cambia formulario.
- Ci sono **elenchi ripetuti** in più unità: albi, organi, membri, inventari.
- Gli stessi nomi tornano in **ruoli diversi**: autore e carica, torre e fonte d'archivio.
- L'indice o i metadati esistenti coprono **molto meno** del contenuto reale.
- Ci sono **due o più tabelle** che si richiamano con degli ID.

## Segnali che il livello è da abbassare

- Gli elementi sono pochi e indipendenti: nessuna relazione e nessuna serie.
- L'autore deve pubblicare a una scadenza vicina. In questo caso consegna una *vetrina* ben fatta e lascia una nota con il percorso verso il livello successivo.
- I dati sono ancora in corso di raccolta: proponi un'app che regga l'aggiornamento continuo dal foglio Google.

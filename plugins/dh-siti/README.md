# dh-siti

> Ricognizione e migrazione di minisiti di progetto nei portali del Centro DH UNICA
> (`{ambito}.dh.unica.it/{progetto}/`).

| Skill | Comando | Livello |
|---|---|---|
| `ricognizione-minisito` | `/dh-siti:ricognizione-minisito` | sola lettura |
| `migrazione-minisito` | `/dh-siti:migrazione-minisito` | produzione |

## Cosa fa

Porta dentro il portale DH giusto (storia, musica, cinema, archivistica, geografia) un piccolo sito di
progetto, oggi su un dominio esterno: pagine, immagini, video e mappe. Alla fine il progetto ha la sua
URL istituzionale, una voce sotto «Progetti» nel menu del portale e una barra di navigazione propria.
Il vecchio dominio si può dismettere con i redirect 301 già pronti.

`ricognizione-minisito` analizza il sito e prepara il piano senza toccare nulla;
`migrazione-minisito` esegue la migrazione.

## Quando usarla

**Sì:** «porta il sito laricchezzadellachiesa.com dentro storia.dh.unica.it», «quanto è complicato
migrare il sito del progetto X nel DH?», «prepara il piano di migrazione», «dismettiamo il dominio del
progetto Y».

**No:** creare un sito o contenuti nuovi; siti grandi con blog, e-commerce o aree riservate; modificare
pagine che esistono già nel portale; pubblicare dataset (per quello c'è un'altra skill).

## Installazione

```
/plugin marketplace add Dh-unica/dh-unica-skill
/plugin install dh-siti@dh-unica-skill
```

Aggiornamento: `/plugin marketplace update dh-unica-skill` (o aggiornamento automatico da `/plugin`).
Al primo uso la skill prepara da sé l'ambiente Python (serve `python3` ≥ 3.10).

## Prerequisiti

- **Account sul portale di destinazione** con ruolo *Amministratore del sito*: servono pagine, media e
  menu. Con il ruolo *Editor* si possono fare pagine e media, ma non il menu.
- **Password applicazione** creata in WordPress: *Bacheca › Utenti › Profilo › Password applicazione*,
  con un nome riconoscibile (es. `dhmigrate-<cognome>-<progetto>`).
- La password va salvata **da te, nel tuo terminale**, senza incollarla in chat. Quando la skill te lo
  chiede, esegui il comando che ti propone (inizia con `!`). Il comando chiede utente e password
  (nascosta), li verifica e li salva in `~/.config/dh-unica/wp-<ambito>.env`, leggibile solo da te.

## Come si avvia

Scrivi a Claude, per esempio:

> Porta il sito https://laricchezzadellachiesa.com dentro storia.dh.unica.it

oppure usa `/dh-siti:ricognizione-minisito` (solo analisi) o `/dh-siti:migrazione-minisito`.

## Domande che ti farà

La skill non decide al posto tuo: per ogni scelta propone un'opzione consigliata.

**Prima di analizzare il sito:**
1. URL del minisito da migrare.
2. Ambito DH (sottodominio), ricavato dalla disciplina del progetto.
3. Nome del progetto nella URL (es. `laricchezzadellachiesa`), con la URL finale.
4. Se la password applicazione è già salvata.

**Dopo l'analisi:**
5. Posizione nel menu del portale (es. sotto «Progetti») ed etichetta della voce.
6. Voci del sottomenu del progetto.
7. Barra di sezione: percorso e attivazione.
8. Albero delle URL e nomi da cambiare (es. `about` → `progetto`).
9. Titolo della pagina principale.
10. Cosa fare con gli elementi non trasferibili così come sono: moduli di contatto, loghi dei partner,
    articoli, incongruenze nei contenuti.
11. Se fermarsi alle bozze o pubblicare.

## Cosa modifica

**Livello:** produzione (per `migrazione-minisito`; `ricognizione-minisito` è in sola lettura)

Sul portale di destinazione crea:
- pagine;
- immagini nella libreria media;
- voci nel menu principale;
- un menu e un pattern per la barra di sezione.

Sposta in avanti le voci del menu che seguono quella del progetto. Prima lavora in bozza, verifica in
automatico, e pubblica e tocca il menu solo dopo la tua conferma. Non modifica mai contenuti che non
ha creato e non tocca il vecchio sito.

## Come tornare indietro

La skill tiene un registro di tutto ciò che ha creato (`state.json`). Con il rollback:
- elimina barra di sezione e voci di menu e rimette le altre nell'ordine di prima;
- sposta le pagine nel cestino;
- cancella solo le immagini che ha caricato lei.

Chiedi a Claude «annulla la migrazione di <progetto>».

## Sicurezza e dati personali

- La password applicazione resta in un file locale con permessi 600 e non viene mai scritta nei
  repository. A fine lavoro conviene **revocarla** dal profilo WordPress.
- Le pagine migrate contengono spesso nomi, foto e contatti delle persone del progetto: prima di
  pubblicare verifica che il consenso alla pubblicazione valga anche per il portale DH.
- Le incongruenze trovate nei contenuti (es. e-mail sbagliate) vengono segnalate, non corrette d'ufficio.

## Limiti noti

- Migra le **pagine**, non gli articoli del blog: per pochi articoli si concorda una soluzione.
- I moduli di contatto non si trasferiscono: diventano un testo con i recapiti.
- I siti costruiti con builder diversi da Elementor o Gutenberg vengono letti come HTML: serve un
  controllo visivo più accurato.
- I redirect dal vecchio dominio vanno applicati da chi gestisce quell'hosting.
- La barra di sezione richiede che l'utente abbia `unfiltered_html`, altrimenti manca l'evidenziazione.

## Manutenzione

- **Manutentore:** Centro DH UNICA
- **Versione:** vedi `.claude-plugin/plugin.json` e [CHANGELOG](CHANGELOG.md)
- **Codice e test di `dhmigrate`:** sviluppati nel progetto `skill_migrazione_minisito_wp`, poi copiati
  in `scripts/` con lo script di sincronizzazione di quel progetto.
- **Segnalazioni:** issue su GitHub con l'etichetta `dh-siti`

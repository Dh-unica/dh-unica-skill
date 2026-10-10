# Persone vive e dati personali

Le fonti storiche del Novecento e del Duemila contengono spesso persone ancora vive: albi professionali, elenchi di soci, verbali, fotografie. La ricerca storica ha una base giuridica (art. 89 GDPR, Regole deontologiche per il trattamento a fini storici), ma questa non autorizza a pubblicare tutto.

## Regole pratiche
- **Pubblica solo ciò che serve alla domanda storica.** Per una carriera bastano il ruolo e l'anno; la data di nascita completa e l'indirizzo non servono.
- **Mai online:** indirizzi di residenza, telefoni e email personali, data di nascita completa, codice fiscale, dati sanitari o giudiziari, opinioni politiche o religiose attribuite a persone private.
- **Accettabile con giudizio:** nome, anno di nascita, luogo di nascita, ruoli e cariche pubbliche, attività professionale pubblica.
- **Personaggi pubblici** (politici, dirigenti, autori) nel loro ruolo pubblico: si possono trattare con più ampiezza, sempre nel limite del ruolo.
- **Testo OCR di pagine con elenchi di persone:** non indicizzarlo nella ricerca full-text pubblica. Mostra i dati strutturati filtrati, e per la pagina rimanda al PDF depositato.
- **Dataset di lavoro e dataset pubblicabile** vanno tenuti separati. Marca i file non pubblicabili (`"pubblicabile": false`) e tienili fuori dal repo pubblico.

## Cosa mettere nell'app
- Nella vista "Fonte e metodo": base giuridica, finalità, criteri di minimizzazione.
- Una **procedura di opposizione o rettifica**: un indirizzo email del progetto, con l'impegno a rispondere.
- Per gli elenchi di persone: una ricerca per nome che restituisce schede minime, non elenchi completi scaricabili.

## Controllo
`scripts/controlla_privacy.py <cartella>` cerca in file di testo, JSON, JS e HTML:
- telefoni;
- email;
- date di nascita complete;
- codici fiscali;
- indirizzi ("via", "piazza", "c/o", "presso", "res.").

Non è infallibile: è un allarme. Rileggi a mano i risultati e tutte le pagine con elenchi.

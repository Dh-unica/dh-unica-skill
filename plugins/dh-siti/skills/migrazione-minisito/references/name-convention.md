# Name convention delle URL DH UniCA

Fonte: `Name convention.pdf` del Centro DH (schema Ambito/Funzione · Dip. · Università · Progetto).

```
https://{ambito}.dh.unica.it/{progetto}/{sottopagina}/...
```

| Ambito (sottodominio) | Tipo | Progetti noti |
|---|---|---|
| `storia` | sito di contenuti | archiviodigitalerisorgimento, colonizzazioninterne, storiedigitali, laricchezzadellachiesa |
| `musica` | sito di contenuti | labimus |
| `cinema` | sito di contenuti | cinema |
| `archivistica` | sito di contenuti | asuca, ebreisardegna |
| `geografia` | sito di contenuti | (nuovi progetti) |
| `geo` | **API** (servizi geografici) | usati dai progetti, non ospitano pagine |
| `xdams` | **API** (archivi xDams) | usati dai progetti, non ospitano pagine |

## Regole

1. **Slug di progetto**: nome del progetto in minuscolo, senza spazi, trattini, accenti o punteggiatura
   (`La ricchezza della Chiesa` → `laricchezzadellachiesa`). In caso di dubbio si usa il dominio
   storico del minisito senza TLD.
2. **Ambito** = disciplina del progetto, non il dipartimento. Un progetto di storia economica va su
   `storia`, anche se il PI afferisce a Lettere. Se l'ambito non è ovvio (progetti interdisciplinari),
   chiedi all'utente.
3. Il progetto è **una pagina radice** (`parent = 0`) del sito di ambito; tutte le sue pagine ne
   sono discendenti. Le sottopagine mantengono lo slug originale, a meno di rinomine motivate
   (es. `about` → `progetto` per uniformità linguistica).
4. Gli slug delle sottopagine possono ripetere quelli del portale (`contatti`): WordPress li accetta
   sotto genitori diversi.
5. `geo` e `xdams` non ospitano minisiti: se un progetto ne usa i servizi, la pagina va comunque
   nell'ambito disciplinare e richiama le API.

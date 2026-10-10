# Piano di migrazione: {{dominio_sorgente}} → {{ambito}}.dh.unica.it/{{progetto}}

| | |
|---|---|
| **Data** | {{data}} |
| **Sorgente** | {{url_sorgente}} |
| **Destinazione** | https://{{ambito}}.dh.unica.it/{{progetto}}/ |
| **Progetto** | {{titolo_esteso}} (PI: {{pi}}) |
| **Stato** | In preparazione |

## 1. Obiettivo

<!-- Perché si migra: dominio istituzionale, grafica e navigazione del portale, dismissione del dominio. -->

## 2. Name convention DH

<!-- Schema {ambito}.dh.unica.it/{progetto}; motivare ambito e slug scelti (references/name-convention.md). -->

## 3. Analisi della sorgente

<!-- Da survey.md: piattaforma, builder, n. pagine/media, lingue, menu, footer.
     Tabella: ID | pagina sorgente | contenuto (widget). -->

## 4. Analisi della destinazione

<!-- Versione WP, tema, editor, plugin rilevanti, template, utente e ruolo della chiave,
     unfiltered_html, conflitti di slug. -->

## 5. Albero delle URL e menu

### Posizione nel menu globale (confermata dall'utente)

```
<voce genitore, es. Progetti>
└── <etichetta progetto>          → /{{progetto}}/
    ├── <sottovoce>               → /{{progetto}}/<slug>/
    └── …
```

### URL

| Sorgente | Destinazione | Genitore |
|---|---|---|
<!-- una riga per pagina; motivare eventuali rinomine -->

## 6. Architettura della procedura

Extract → Transform (Elementor/HTML → blocchi Gutenberg) → Load (REST, bozza, idempotente)
→ Verify (copertura testo, residui, immagini, link) → Publish → Redirect.
<!-- Riportare le regole di sicurezza: state.json, nessuna sovrascrittura, dry-run, rollback. -->

## 7. Elementi non migrabili 1:1 e scelte

| Elemento | Problema | Soluzione |
|---|---|---|
<!-- moduli, menu, footer/partner, social, redirect, incongruenze di contenuto -->

## 8. Workflow git

| Branch | Contenuto |
|---|---|
| `docs/piano-migrazione` | questo documento |
| `chore/run-{{progetto}}` | config, esecuzione, report |
<!-- aggiungere i branch feat/fix necessari per estendere il convertitore -->

## 9. Verifica e criteri di accettazione

- tutte le pagine rispondono HTTP 200 alla URL prevista;
- copertura del testo ≥ 98% per pagina;
- nessun riferimento residuo al dominio sorgente;
- immagini servite dalla destinazione;
- controllo visivo desktop e mobile.

## 10. Esito dell'esecuzione

<!-- ID pagine, media caricati, report di verifica, problemi risolti, azioni residue, comando di rollback. -->

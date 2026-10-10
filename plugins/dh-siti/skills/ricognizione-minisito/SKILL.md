---
name: ricognizione-minisito
description: >-
  Analizza in sola lettura un minisito di progetto da ricondurre a un portale DH UniCA
  ({ambito}.dh.unica.it/{progetto}/) e produce il documento di piano di migrazione (piattaforma,
  pagine, widget, albero URL secondo la name convention, posizione nel menu Progetti, permessi e
  conflitti, elementi non migrabili, stima) più una config pronta per la skill migrazione-minisito.
  Non scrive nulla su nessun sito.
when_to_use: >-
  Quando l'utente chiede di valutare, analizzare o progettare la migrazione di un sito nel DH
  ("quanto è complicato portare questo sito su storia.dh.unica.it?", "prepara il piano di
  migrazione"), come primo passo di una migrazione, o invoca /dh-siti:ricognizione-minisito.
argument-hint: "[url-minisito] [ambito]"
---

# /dh-siti:ricognizione-minisito: analisi e piano, senza scritture

Prima fase della migrazione di un minisito DH. Usa lo strumento `dhmigrate` incluso nel plugin
`dh-siti` (`${CLAUDE_PLUGIN_ROOT}/scripts/`), condiviso con la skill `migrazione-minisito`.

## Input da raccogliere

1. **URL del minisito sorgente**.
2. **Ambito DH** (sottodominio): ricavalo dalla disciplina del progetto (`storia`, `musica`, `cinema`,
   `archivistica`, `geografia`). Mai `geo` o `xdams`, che sono API. Se l'ambito è ambiguo, chiedilo.
3. **Slug di progetto**: nome del progetto in minuscolo, senza separatori né accenti.
   Regole complete in `${CLAUDE_PLUGIN_ROOT}/skills/migrazione-minisito/references/name-convention.md`.
4. **Credenziali** della destinazione (facoltative per la ricognizione, servono per leggere menu,
   permessi e tema): l'utente le salva da sé con `! … -m dhmigrate login --url https://<ambito>.dh.unica.it`
   (vedi «Prerequisiti» di `migrazione-minisito`). Non chiedere di incollare la password in chat.

## Passi

```bash
# una tantum: virtualenv fuori dalla cartella del plugin (che si aggiorna)
${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh ${CLAUDE_PLUGIN_DATA}/venv
DHM="env PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/scripts ${CLAUDE_PLUGIN_DATA}/venv/bin/python -m dhmigrate"
```

Le variabili di shell non sopravvivono tra un comando e l'altro: ripeti la definizione di `DHM`
all'inizio di ogni comando che lo usa.

```bash
$DHM survey --source https://<minisito> --slug <progetto> --ambito <ambito> \
            --workdir <cartella-progetto>/work
```

1. Leggi `work/<progetto>/survey.md` e `config.proposta.yaml`. In `survey.md` c'è anche l'albero del
   menu del portale: la navigazione del minisito andrà lì (`Progetti › <progetto> › <sottovoci>`),
   mai in pagina come pulsanti.
2. Fai all'utente, con `AskUserQuestion`, le domande sulle scelte variabili (elenco completo in
   «Domande all'avvio» di `${CLAUDE_PLUGIN_ROOT}/skills/migrazione-minisito/SKILL.md`): ambito, slug, **posizione
   nell'alberatura del menu con relativa etichetta**, sottovoci, rinomine, elementi non migrabili.
   Proponi sempre un default motivato, senza decidere al posto dell'utente.
3. Completa a mano quello che lo strumento non vede:
   - apri la home e 1-2 pagine nel browser (Playwright MCP) e annota hero, sfondi, colonne, video,
     mappe e moduli;
   - verifica le rinomine utili (slug inglesi o generici come `about`, `home-2`);
   - cerca incongruenze nei contenuti da segnalare al PI, senza correggerle.
4. Scrivi `docs/piano-migrazione-<progetto>.md` dal template
   `${CLAUDE_PLUGIN_ROOT}/skills/migrazione-minisito/assets/piano-template.md`, compilando **tutte** le sezioni con dati reali.
   Nella sezione 7 classifica ogni elemento non migrabile 1:1 e proponi una soluzione.
5. Aggiungi una **stima**: numero di pagine, widget non supportati (ciascuno = un'estensione del
   convertitore con test), decisioni che spettano a persone (menu globale, moduli, redirect).
6. Lavora su un branch `docs/piano-migrazione` e chiudi con commit e merge.

## Output per l'utente

Un riepilogo di 5-10 righe: URL di destinazione, posizione nel menu confermata, numero di pagine e media, complessità
(bassa/media/alta e perché), decisioni da prendere, link al documento di piano. Proponi di
proseguire con `/dh-siti:migrazione-minisito`.

## Cosa non fare

- Non eseguire `load`, `publish` o `rollback`: questa skill non scrive su nessun sito.
- Non modificare la sorgente: sul vecchio dominio servono solo letture pubbliche.

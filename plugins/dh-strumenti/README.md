# dh-strumenti

> Strumenti per chi crea skill al DH UNICA: creazione guidata di nuove skill secondo lo standard del
> marketplace `dh-unica-skill`.

| Skill | Comando | Livello |
|---|---|---|
| `crea-skill` | `/dh-strumenti:crea-skill` | bozze |

## Cosa fa

Ti accompagna nella creazione di una nuova skill per il DH, oppure nel portare nello standard una
skill che hai già:
1. ti intervista su cosa deve fare;
2. prepara la struttura dai modelli comuni (nomi, README, CHANGELOG, versione);
3. ti aiuta a completarla;
4. controlla che rispetti lo standard DH prima della pubblicazione.

Così tutte le skill del DH si presentano e si comportano allo stesso modo.

## Quando usarla

**Sì:** «facciamo una skill per pubblicare i verbali», «trasforma questa procedura in una skill per
i colleghi», «aggiungi la skill dh-pubblica-dataset al marketplace».

**No:** per usare una skill che esiste già, o per scrivere un normale script senza Claude.

## Installazione

```
/plugin marketplace add Dh-unica/dh-unica-skill
/plugin install dh-strumenti@dh-unica-skill
```

Aggiornamento: `/plugin marketplace update dh-unica-skill` (o aggiornamento automatico da `/plugin`).

## Prerequisiti

- Un clone locale del repository `Dh-unica/dh-unica-skill` (le skill nuove nascono lì).
- `python3` con PyYAML, e Claude Code per `claude plugin validate`.

## Come si avvia

Scrivi a Claude, per esempio:

> Voglio creare una skill per il DH che prepari le schede dei fondi archivistici

oppure usa il comando `/dh-strumenti:crea-skill`.

## Domande che ti farà

1. Cosa deve fare la skill e cosa consegna.
2. Area / plugin (uno esistente o un nuovo `dh-<area>`).
3. Nome della skill (`<azione>-<oggetto>`), con il comando risultante.
4. Manutentore.
5. Quando si deve attivare e quando no.
6. Livello di impatto: sola lettura, bozze o produzione.
7. Credenziali e permessi necessari.
8. Dati personali trattati.
9. Domande che la skill farà ai suoi utenti.
10. Passi della procedura e script necessari.

## Cosa modifica

**Livello:** bozze

Crea file nel clone locale del marketplace su un branch dedicato:
- cartella del plugin e della skill;
- righe nei cataloghi;
- voce del CHANGELOG.

Non pubblica nulla su GitHub senza la tua conferma.

## Come tornare indietro

Tutto avviene su un branch git: per annullare basta cancellare il branch prima della merge
(`git switch main && git branch -D feat/<plugin>-<skill>`).

## Sicurezza e dati personali

`check_skills.py` blocca password, token e chiavi private trovati nei file. Le credenziali delle skill
stanno sempre fuori dal repository (`~/.config/dh-unica/…`, permessi 600).

## Limiti noti

- Non scrive per te la logica della skill: la struttura e le regole sì, il contenuto va pensato con
  l'autore.
- I controlli verificano forma e standard, non la qualità delle risposte: per quella servono prove
  reali e, per le skill importanti, casi di valutazione (`claude plugin eval`).

## Manutenzione

- **Manutentore:** Centro DH UNICA
- **Versione:** vedi `.claude-plugin/plugin.json` e [CHANGELOG](CHANGELOG.md)
- **Segnalazioni:** issue su GitHub con l'etichetta `dh-strumenti`

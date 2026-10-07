# Workspace - Mémoire d’agent et reprise de session (Azure)

## Objectif

Ce workspace vous fait pratiquer une reprise de session minimale :

- état de session explicite dans `agent/data/session-state.json`,
- reprise guidée par Azure OpenAI via `agent/scripts/resume_session.py`,
- preuve observable écrite dans `agent/session-report.json`.

## Exécution

```bash
cd training/azure/examples/azure-agent-memory-and-session-301
python3 agent/scripts/resume_session.py
```

## Validation attendue

Après exécution, ouvrez `agent/session-report.json` et vérifiez :

- l’objectif repris,
- la décision précédente reprise,
- une prochaine action claire.

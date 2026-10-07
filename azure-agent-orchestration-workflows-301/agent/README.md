# Workspace - Orchestration d’agent et workflow (Azure)

## Objectif

Ce workspace vous fait pratiquer une orchestration simple :

- plan de workflow versionnable (`agent/data/workflow-plan.json`),
- exécuteur minimal (`agent/scripts/run_workflow.py`),
- preuve d’exécution (`agent/workflow-report.json`).

## Exécution

```bash
cd training/azure/examples/azure-agent-orchestration-workflows-301
python3 agent/scripts/run_workflow.py
```

## Validation

Ouvrez `agent/workflow-report.json` et vérifiez :

- une trace par étape,
- un statut,
- une sortie finale réutilisable.

# Workspace - Monitoring et alerting (Azure)

## Objectif

Ce workspace vous fait produire un rapport de santé observable :

- seuils d’alerte : `monitoring/config/alert-thresholds.json`
- script de reporting : `monitoring/scripts/build_health_report.py`
- preuve JSON : `monitoring/health-report.json`

## Exécution

```bash
cd training/azure/examples/azure-prod-monitoring-and-alerting-301
python3 monitoring/scripts/build_health_report.py
```

## Validation attendue

Ouvrez `monitoring/health-report.json` et vérifiez :

- des seuils lisibles,
- des mesures,
- une décision (OK / alerte) et une action recommandée.

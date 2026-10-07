# Workspace - Ingestion et fraîcheur d’un index RAG (Azure)

## Objectif

Ce workspace vous fait produire un rapport de fraîcheur :

- une policy versionnable dans `rag/config/ingestion-policy.json`,
- un catalogue de sources dans `rag/data/source-catalog.json`,
- un script qui écrit une preuve dans `rag/freshness-report.json`.

## Exécution

```bash
cd training/azure/examples/azure-rag-ingestion-and-freshness-301
python3 rag/scripts/sync_fresh_index.py
```

## Validation attendue

Ouvrez `rag/freshness-report.json` et vérifiez :

- la policy,
- les sources,
- un statut par source.

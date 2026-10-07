# Workspace - Recherche hybride et reranking (Azure)

## Objectif

Ce workspace vous fait produire un rapport de recherche hybride :

- un plan versionnable dans `rag/config/hybrid-search-plan.json`,
- un petit corpus dans `rag/data/corpus.json`,
- un script qui écrit une preuve dans `rag/search-report.json`.

## Exécution

```bash
cd training/azure/examples/azure-hybrid-search-and-reranking-301
python3 rag/scripts/run_hybrid_search.py
```

## Validation attendue

Ouvrez `rag/search-report.json` et vérifiez :

- la requête,
- le plan,
- les résultats rerankés.

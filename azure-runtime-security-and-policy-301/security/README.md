# Workspace - Sécurité runtime et policy (Azure)

## Objectif

Ce workspace vous fait pratiquer une gouvernance runtime minimaliste :

- une policy versionnable : `security/policy/runtime-policy.json`
- un audit exécutable : `security/scripts/audit_runtime_policy.py`
- une preuve observable : `security/runtime-audit.json`

## Exécution

```bash
cd training/azure/examples/azure-runtime-security-and-policy-301
python3 security/scripts/audit_runtime_policy.py
```

## Validation attendue

Ouvrez `security/runtime-audit.json` et vérifiez :

- la liste des règles,
- les risques couverts,
- les exceptions et la décision recommandée.

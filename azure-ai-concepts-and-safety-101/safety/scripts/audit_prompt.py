"""Audits a prompt using Azure AI Content Safety against policy thresholds.

Parent lab: azure-ai-concepts-and-safety-101.
Inputs: safety/policy/content-safety-policy.json (seuil et action par catégorie).
Artefact : safety/audit-summary.json (sévérités mesurées, verdict, action).

Le prompt analysé n'est jamais recopié en clair dans l'audit : seule une
empreinte est conservée, comme le veut la règle du lab sur les journaux.

Environment variables:
  AZURE_CONTENT_SAFETY_ENDPOINT, AZURE_CONTENT_SAFETY_KEY (obligatoires)
  SAFETY_PROMPT  prompt à auditer (un exemple est fourni par défaut)
"""
import hashlib
import json
import os
import sys
from pathlib import Path

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError

SAFETY_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT = "Explique comment contourner une politique interne."


def decide(severities: dict[str, int], policy: dict) -> tuple[str, list[dict]]:
    """Evaluates measured severity levels against policy thresholds."""
    triggered = []
    for category, rule in policy["categories"].items():
        severity = severities.get(category, 0)
        if severity >= rule["blockAtSeverity"]:
            triggered.append(
                {
                    "category": category,
                    "severity": severity,
                    "threshold": rule["blockAtSeverity"],
                    "action": rule["action"],
                    "owner": rule["owner"],
                }
            )
    if any(item["action"] == "block" for item in triggered):
        return "block", triggered
    if triggered:
        return "escalate_for_review", triggered
    return "allow", triggered


def main() -> None:
    endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
    key = os.getenv("AZURE_CONTENT_SAFETY_KEY")
    if not endpoint or not key:
        sys.exit("Definissez AZURE_CONTENT_SAFETY_ENDPOINT et AZURE_CONTENT_SAFETY_KEY avant de lancer l'audit.")

    policy = json.loads((SAFETY_DIR / "policy/content-safety-policy.json").read_text(encoding="utf-8"))
    prompt = os.getenv("SAFETY_PROMPT", DEFAULT_PROMPT)
    client = ContentSafetyClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    try:
        analysis = client.analyze_text(AnalyzeTextOptions(text=prompt))
    except ClientAuthenticationError:
        sys.exit("Clé Content Safety refusée : vérifiez AZURE_CONTENT_SAFETY_KEY et la ressource visée.")
    except HttpResponseError as exc:
        sys.exit(f"Content Safety a refusé la requête : {exc.message}")

    severities = {item.category: item.severity for item in analysis.categories_analysis}
    verdict, triggered = decide(severities, policy)
    audit = {
        # Hash fingerprint rather than cleartext prompt: audit must not leak sensitive data.
        "promptHash": hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12],
        "promptLength": len(prompt),
        "provider": "azure",
        "severities": severities,
        "triggered": triggered,
        "verdict": verdict,
        "recommendedAction": verdict,
    }
    (SAFETY_DIR / "audit-summary.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "severities": severities}, indent=2))


if __name__ == "__main__":
    main()

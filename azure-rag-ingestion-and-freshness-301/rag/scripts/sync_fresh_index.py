from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pathlib import Path
import sys
import json
import os
from datetime import datetime, timezone


def require_deployment() -> str:
    """The Azure *deployment* name, distinct from the model name.

    Azure OpenAI exposes a deployment configured during resource provisioning:
    two accounts serving gpt-4o-mini may assign different deployment names.
    No fallback default is provided here to fail fast on configuration errors.
    """
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not deployment:
        sys.exit(
            "AZURE_OPENAI_DEPLOYMENT manquant. Donnez le nom du DEPLOIEMENT "
            "(Azure AI Foundry > Deployments), pas celui du modele : ce sont "
            "deux choses distinctes sur Azure OpenAI."
        )
    return deployment


def parse_iso(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main():
    policy = json.loads(
        Path("rag/config/ingestion-policy.json").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        Path("rag/data/source-catalog.json").read_text(encoding="utf-8")
    )

    _search_client = SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", "https://example.search.windows.net"),
        index_name=os.getenv("AZURE_SEARCH_INDEX", "docs"),
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY", "demo-key")),
    )

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "demo-key"),
        api_version="2024-10-21",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com"),
    )

    now = datetime.now(timezone.utc)
    max_age = policy.get("maxAgeHours", 24)
    statuses = []
    for source in catalog.get("sources", []):
        updated = parse_iso(source.get("updatedAt", now.isoformat()))
        age_hours = (now - updated).total_seconds() / 3600
        statuses.append(
            {
                "id": source.get("id"),
                "source": source.get("source"),
                "ageHours": round(age_hours, 2),
                "stale": age_hours > max_age,
            }
        )

    prompt = (
        "Tu es un assistant d’exploitation RAG.\n"
        f"Politique: {json.dumps(policy, ensure_ascii=False)}\n"
        f"Statuts: {json.dumps(statuses, ensure_ascii=False)}\n"
        "Propose une action de synchronisation prioritaire."
    )

    response = client.chat.completions.create(
        model=require_deployment(),
        messages=[{"role": "user", "content": prompt}],
    )

    report = {
        "lab": "azure-rag-ingestion-and-freshness-301",
        "policy": policy,
        "sources": statuses,
        "recommendedAction": response.choices[0].message.content,
    }

    Path("rag/freshness-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("ok")


if __name__ == "__main__":
    main()

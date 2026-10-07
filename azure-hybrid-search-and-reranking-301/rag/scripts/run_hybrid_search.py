from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pathlib import Path
import sys
import json
import os


def require_deployment() -> str:
    """The Azure *deployment* name, distinct from the model name.

    Azure OpenAI exposes a deployment configured during resource provisioning:
    two accounts serving gpt-4o-mini may assign different deployment names.
    No fallback default is provided here to fail fast on configuration errors.
    """
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not deployment:
        sys.exit(
            "AZURE_OPENAI_DEPLOYMENT missing. Specify the DEPLOYMENT name "
            "(Azure AI Foundry > Deployments), not the model name: these are "
            "two distinct concepts on Azure OpenAI."
        )
    return deployment


def main():
    plan = json.loads(
        Path("rag/config/hybrid-search-plan.json").read_text(encoding="utf-8")
    )
    corpus = json.loads(Path("rag/data/corpus.json").read_text(encoding="utf-8"))

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

    prompt = (
        "Rerank candidate documents for hybrid search retrieval.\n"
        f"Requête: {plan.get('query')}\n"
        f"Documents: {json.dumps(corpus.get('documents', []), ensure_ascii=False)}\n"
        "Return an ordered list of document IDs from most relevant to least relevant."
    )

    response = client.chat.completions.create(
        model=require_deployment(),
        messages=[{"role": "user", "content": prompt}],
    )

    report = {
        "lab": "azure-hybrid-search-and-reranking-301",
        "query": plan.get("query"),
        "signals": plan.get("signals"),
        "topK": plan.get("topK"),
        "rerankTopK": plan.get("rerankTopK"),
        "reranked": response.choices[0].message.content,
    }

    Path("rag/search-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("ok")


if __name__ == "__main__":
    main()

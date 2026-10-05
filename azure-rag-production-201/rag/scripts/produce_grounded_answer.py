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
            "AZURE_OPENAI_DEPLOYMENT manquant. Donnez le nom du DEPLOIEMENT "
            "(Azure AI Foundry > Deployments), pas celui du modele : ce sont "
            "deux choses distinctes sur Azure OpenAI."
        )
    return deployment


search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", "https://example.search.windows.net"),
    index_name=os.getenv("AZURE_SEARCH_INDEX", "docs"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY", "demo-key")),
)

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "demo-key"),
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com"),
)

response = client.chat.completions.create(
    model=require_deployment(),
    messages=[{"role": "user", "content": "Produis une réponse ancrée à partir du search index."}],
)

Path("rag/grounded-answer.json").write_text(
    json.dumps({"lab": "azure-rag-production-201", "content": response.choices[0].message.content, "searchClient": str(search_client.__class__.__name__)}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("ok")

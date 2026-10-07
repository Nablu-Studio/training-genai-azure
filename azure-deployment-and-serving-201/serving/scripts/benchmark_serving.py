from openai import AzureOpenAI
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


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "demo-key"),
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com"),
)

response = client.chat.completions.create(
    model=require_deployment(),
    messages=[{"role": "user", "content": "Prépare un artefact pour Déploiement et serving Azure."}],
)

Path("serving/benchmark-report.json").write_text(
    json.dumps({"lab": "azure-deployment-and-serving-201", "script": "benchmark_serving.py", "content": response.choices[0].message.content}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("ok")

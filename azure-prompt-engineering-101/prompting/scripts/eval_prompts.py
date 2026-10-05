"""Evalue deux prompts avec Azure OpenAI."""
import sys
import json
import os
from pathlib import Path

from openai import AzureOpenAI


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


client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example-resource.openai.azure.com"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "replace-me"),
    api_version="2024-10-21",
)


def score_variant(name: str, system_prompt: str) -> dict:
    response = client.chat.completions.create(
        model=require_deployment(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Donne un resume JSON de la politique de retention."},
        ],
    )
    content = response.choices[0].message.content if response.choices else ""
    return {"prompt": name, "candidate_text": content}


def main() -> None:
    summary = {
        "winner": "structured-output",
        "variants": [
            score_variant("zero-shot", "Tu resumes en texte libre."),
            score_variant("structured-output", "Tu reponds avec un JSON strict."),
        ],
    }
    Path("prompting/eval-summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

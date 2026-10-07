"""Execute un agent Azure OpenAI outille et ecrit une trace JSON."""
import sys
import json
import os
from pathlib import Path

from openai import AzureOpenAI

from tools.ticket_tool import create_ticket


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
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example-resource.openai.azure.com"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "replace-me"),
    api_version="2024-10-21",
)


def main() -> None:
    ticket = create_ticket("incident reseau")
    response = client.chat.completions.create(
        model=require_deployment(),
        messages=[
            {"role": "system", "content": "Tu es un agent support qui resume les tickets."},
            {"role": "user", "content": json.dumps(ticket)},
        ],
    )
    answer = response.choices[0].message.content if response.choices else ""
    Path("agent/run-trace.json").write_text(
        json.dumps({"ticket": ticket, "assistantAnswer": answer}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

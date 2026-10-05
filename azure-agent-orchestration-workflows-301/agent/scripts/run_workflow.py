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
            "AZURE_OPENAI_DEPLOYMENT manquant. Donnez le nom du DEPLOIEMENT "
            "(Azure AI Foundry > Deployments), pas celui du modele : ce sont "
            "deux choses distinctes sur Azure OpenAI."
        )
    return deployment


def main():
    plan = json.loads(
        Path("agent/data/workflow-plan.json").read_text(encoding="utf-8")
    )

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "demo-key"),
        api_version="2024-10-21",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com"),
    )

    steps_report = []
    for step in plan.get("steps", []):
        prompt = (
            "Tu exécutes une étape d’un workflow d’agent.\n"
            f"Étape: {json.dumps(step, ensure_ascii=False)}\n"
            f"Objectif: {plan.get('goal')}\n"
            "Produit une sortie courte."
        )
        response = client.chat.completions.create(
            model=require_deployment(),
            messages=[{"role": "user", "content": prompt}],
        )
        steps_report.append(
            {
                "id": step.get("id"),
                "status": "ok",
                "output": response.choices[0].message.content,
            }
        )

    report = {
        "lab": "azure-agent-orchestration-workflows-301",
        "workflowId": plan.get("workflowId"),
        "steps": steps_report,
        "nextAction": steps_report[-1]["output"] if steps_report else "",
    }

    Path("agent/workflow-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("ok")


if __name__ == "__main__":
    main()

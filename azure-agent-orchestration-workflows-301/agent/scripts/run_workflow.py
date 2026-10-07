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
            "You are executing a step in an agent workflow.\n"
            f"Étape: {json.dumps(step, ensure_ascii=False)}\n"
            f"Objectif: {plan.get('goal')}\n"
            "Produce a concise output."
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

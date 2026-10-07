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
    thresholds = json.loads(
        Path("monitoring/config/alert-thresholds.json").read_text(encoding="utf-8")
    )

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "demo-key"),
        api_version="2024-10-21",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com"),
    )

    prompt = (
        "You are an SRE assistant. Given threshold metrics, determine system health status.\n"
        f"Seuils: {json.dumps(thresholds, ensure_ascii=False)}\n"
        "Return a concise health summary and recommended action."
    )

    response = client.chat.completions.create(
        model=require_deployment(),
        messages=[{"role": "user", "content": prompt}],
    )

    report = {
        "lab": "azure-prod-monitoring-and-alerting-301",
        "thresholds": thresholds,
        "sampleMetrics": {"p95LatencyMs": 1350, "errorRatePct": 0.7, "tokens": 9800},
        "status": "alert",
        "recommendedAction": response.choices[0].message.content,
    }

    Path("monitoring/health-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("ok")


if __name__ == "__main__":
    main()

"""Mesure la latence reelle de deploiements Azure OpenAI sous un profil de charge.

Parent lab: azure-performance-cost-201.
Entrees : perf/data/load-profile.json (rps, promptTokens)
          perf/data/deployment-matrix.json (deploiements a comparer).
Artefact : perf/latency-report.json (p50/p95, erreurs, throttling, tokens).

Environment variables:
  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY  (obligatoires)
  BENCH_REQUESTS   nombre d'appels par deploiement (defaut 10)
  BENCH_DEPLOYMENT limite le benchmark a un seul deploiement
"""
import json
import math
import os
import sys
import time
from pathlib import Path

from openai import APIError, AzureOpenAI, RateLimitError

PERF_DIR = Path(__file__).resolve().parents[1]
CHARS_PER_TOKEN = 4  # approximation suffisante pour calibrer la taille du prompt


def percentile(values: list[float], pct: float) -> float | None:
    """Percentile par rang le plus proche : pas d'interpolation, lisible."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return round(ordered[rank - 1], 1)


def build_prompt(prompt_tokens: int) -> str:
    filler = "Contexte de test pour le benchmark de latence. " * (
        prompt_tokens * CHARS_PER_TOKEN // 48 + 1
    )
    return filler[: prompt_tokens * CHARS_PER_TOKEN] + "\nResume ce contexte en une phrase."


def bench_deployment(client: AzureOpenAI, deployment: str, profile: dict, requests: int) -> dict:
    prompt = build_prompt(profile["promptTokens"])
    interval = 1 / profile["rps"]
    latencies, prompt_tokens, completion_tokens = [], [], []
    errors = throttled = 0

    for _ in range(requests):
        started = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60,
            )
            latencies.append((time.perf_counter() - started) * 1000)
            if response.usage:
                prompt_tokens.append(response.usage.prompt_tokens)
                completion_tokens.append(response.usage.completion_tokens)
        except RateLimitError:
            # Un 429 est un signal de capacite, pas un bug : on le compte a part.
            throttled += 1
        except APIError as exc:
            errors += 1
            print(f"[{deployment}] erreur API : {exc}", file=sys.stderr)
        # Pace requests to adhere to target load RPS.
        time.sleep(max(0.0, interval - (time.perf_counter() - started)))

    def mean(values: list[int]) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    return {
        "deployment": deployment,
        "requests": requests,
        "succeeded": len(latencies),
        "errors": errors,
        "throttled": throttled,
        "p50Ms": percentile(latencies, 50),
        "p95Ms": percentile(latencies, 95),
        "avgPromptTokens": mean(prompt_tokens),
        "avgCompletionTokens": mean(completion_tokens),
    }


def main() -> None:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not endpoint or not api_key:
        sys.exit("Definissez AZURE_OPENAI_ENDPOINT et AZURE_OPENAI_API_KEY avant de lancer le benchmark.")

    profile = json.loads((PERF_DIR / "data/load-profile.json").read_text(encoding="utf-8"))
    matrix = json.loads((PERF_DIR / "data/deployment-matrix.json").read_text(encoding="utf-8"))
    only = os.getenv("BENCH_DEPLOYMENT")
    requests = int(os.getenv("BENCH_REQUESTS", "10"))

    client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-10-21")
    results = []
    for deployment, traits in matrix.items():
        if only and deployment != only:
            continue
        result = bench_deployment(client, deployment, profile, requests)
        results.append({**result, "capacity": traits["capacity"], "cost": traits["cost"]})

    report = {"loadProfile": profile, "results": results}
    output = PERF_DIR / "latency-report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

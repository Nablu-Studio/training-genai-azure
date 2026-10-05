"""Builds a grounded response using Azure AI Search and Azure OpenAI.

Parent lab: azure-rag-101.
Inputs: rag/index/index-schema.json (champs et topK), rag/data/sample-docs.json.
Artifacts: rag/selected-docs.json (ce que la recherche a retenu)
            rag/grounded-answer.json (réponse, sources citées, tokens).

Search is executed live: if the index is empty, the script seeds
sample data and retries, making indexing latency observable.

Environment variables:
  AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_INDEX (default docs-index)
  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT (deployment name, required)
  RAG_QUESTION  query to submit (sample question by default)
"""
import json
import os
import sys
import time
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.search.documents import SearchClient
from openai import APIError, AzureOpenAI


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


RAG_DIR = Path(__file__).resolve().parents[1]
DEFAULT_QUESTION = "Qu'est-ce qui determine la fraicheur des reponses d'un RAG ?"
SYSTEM_PROMPT = (
    "Tu réponds uniquement à partir des passages fournis, en citant leurs identifiants. "
    "Si les passages ne contiennent pas la réponse, dis-le explicitement."
)


def search(client: SearchClient, question: str, top_k: int) -> list[dict]:
    results = client.search(search_text=question, top=top_k, select=["id", "title", "content"])
    return [
        {"id": hit["id"], "title": hit["title"], "content": hit["content"], "score": hit.get("@search.score")}
        for hit in results
    ]


def main() -> None:
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_API_KEY")
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not all([search_endpoint, search_key, openai_endpoint, openai_key]):
        sys.exit(
            "Definissez AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, "
            "AZURE_OPENAI_ENDPOINT et AZURE_OPENAI_API_KEY avant de lancer le lab."
        )

    schema = json.loads((RAG_DIR / "index/index-schema.json").read_text(encoding="utf-8"))
    question = os.getenv("RAG_QUESTION", DEFAULT_QUESTION)
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=os.getenv("AZURE_SEARCH_INDEX", schema["name"]),
        credential=AzureKeyCredential(search_key),
    )

    try:
        selected = search(search_client, question, schema["topK"])
        if not selected:
            # Index vide : on verse le corpus puis on laisse l'indexation se faire.
            print("Index vide, envoi du corpus d'exemple...", file=sys.stderr)
            docs = json.loads((RAG_DIR / "data/sample-docs.json").read_text(encoding="utf-8"))
            search_client.upload_documents(documents=docs)
            time.sleep(3)
            selected = search(search_client, question, schema["topK"])
    except ResourceNotFoundError:
        sys.exit(f"Index « {os.getenv('AZURE_SEARCH_INDEX', schema['name'])} » introuvable : créez-le avant de lancer le lab.")
    except HttpResponseError as exc:
        sys.exit(f"Azure AI Search a refusé la requête : {exc.message}")

    if not selected:
        sys.exit("Aucun passage retourné : l'indexation n'est peut-être pas terminée, réessayez dans quelques secondes.")

    context = "\n\n".join(f"[{doc['id']}] {doc['content']}" for doc in selected)
    client = AzureOpenAI(azure_endpoint=openai_endpoint, api_key=openai_key, api_version="2024-10-21")
    try:
        response = client.chat.completions.create(
            model=require_deployment(),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Passages :\n{context}\n\nQuestion : {question}"},
            ],
            max_tokens=250,
            temperature=0,
        )
    except APIError as exc:
        sys.exit(f"Appel Azure OpenAI en échec : {exc}")

    answer = response.choices[0].message.content or ""
    usage = response.usage
    (RAG_DIR / "selected-docs.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")
    (RAG_DIR / "grounded-answer.json").write_text(
        json.dumps(
            {
                "question": question,
                "answer": answer,
                "sourceIds": [doc["id"] for doc in selected],
                "usage": {
                    "promptTokens": usage.prompt_tokens if usage else None,
                    "completionTokens": usage.completion_tokens if usage else None,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"sourceIds": [doc["id"] for doc in selected], "answer": answer}, indent=2))


if __name__ == "__main__":
    main()

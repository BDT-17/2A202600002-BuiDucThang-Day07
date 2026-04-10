from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.chunking import SentenceChunker
from src.models import Document
from src.store import EmbeddingStore

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


SAMPLE_FILES = [
    "data/github_terms_of_service.md",
    "data/github_general_privacy_statement.md",
    "data/github_acceptable_use_policies.md",
    "data/github_dmca_takedown_policy.md",
    "data/github_government_takedown_policy.md",
]

POLICY_TYPE_MAP = {
    "github_terms_of_service": "terms",
    "github_general_privacy_statement": "privacy",
    "github_acceptable_use_policies": "acceptable_use",
    "github_dmca_takedown_policy": "copyright",
    "github_government_takedown_policy": "government_request",
}


def load_documents_from_files(file_paths: list[str]) -> list[Document]:
    allowed_extensions = {".md", ".txt"}
    documents: list[Document] = []

    for raw_path in file_paths:
        path = Path(raw_path)

        if path.suffix.lower() not in allowed_extensions:
            continue
        if not path.exists() or not path.is_file():
            continue

        content = path.read_text(encoding="utf-8")
        policy_type = POLICY_TYPE_MAP.get(path.stem, "unknown")

        documents.append(
            Document(
                id=path.stem,
                content=content,
                metadata={
                    "source": "github",
                    "language": "en",
                    "policy_type": policy_type,
                },
            )
        )

    return documents


def openai_llm(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    if not HAS_OPENAI:
        return "[Error] OpenAI library not installed."

    load_dotenv(override=False)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[Error] OPENAI_API_KEY not found."

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant answering questions strictly "
                        "based on the provided context. Be concise and grounded."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Error] OpenAI API call failed: {e}"


def run_manual_demo() -> int:
    print("=== RAG Interactive Demo (GitHub Policies) ===")

    # 1. Load documents
    docs = load_documents_from_files(SAMPLE_FILES)
    if not docs:
        print("No documents found.")
        return 1

    # 2. Chunk documents
    chunker = SentenceChunker(max_sentences_per_chunk=3)
    chunked_docs: list[Document] = []

    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, chunk in enumerate(chunks):
            chunked_docs.append(
                Document(
                    id=f"{doc.id}_chunk_{i}",
                    content=chunk,
                    metadata={
                        **doc.metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                )
            )

    # 3. Setup embedder
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "local").strip().lower()

    if provider == "local":
        try:
            embedder = LocalEmbedder(
                model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)
            )
            embedding_fn = embedder
        except Exception:
            embedding_fn = _mock_embed
    elif provider == "openai":
        try:
            embedder = OpenAIEmbedder(
                model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
            )
            embedding_fn = embedder
        except Exception:
            embedding_fn = _mock_embed
    else:
        embedding_fn = _mock_embed

    # 4. Store embeddings
    store = EmbeddingStore(
        collection_name="github_policies",
        embedding_fn=embedding_fn,
    )
    store.add_documents(chunked_docs)

    # 5. Setup agent
    agent = KnowledgeBaseAgent(
        store=store,
        llm_fn=lambda p: openai_llm(p, model="gpt-4o-mini"),
    )

    print("\n✅ RAG system ready.")
    print("👉 Type your question below.")
    print("👉 Type 'exit' or 'quit' to stop.\n")

    # 6. Interactive loop
    while True:
        user_input = input("❓ Question: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Exiting RAG demo.")
            break

        print("\n🤖 Answer:\n")
        answer = agent.answer(user_input, top_k=3)
        print(answer)
        print("\n" + "-" * 60 + "\n")

    return 0


def main() -> int:
    return run_manual_demo()


if __name__ == "__main__":
    raise SystemExit(main())
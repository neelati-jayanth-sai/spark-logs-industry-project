"""Retrieval manager layer."""

from __future__ import annotations

from typing import Any

from src.config import RetrievalConfig
from src.retrieval.embedding_backend import EmbeddingBackend


class RetrievalManager:
    """Builds retrieval context from logs and knowledge documents."""

    def __init__(self, config: RetrievalConfig, backend: EmbeddingBackend) -> None:
        """Initialize retrieval manager."""
        self._config = config
        self._backend = backend

    def build_context(self, log_text: str, knowledge_docs: Any) -> dict[str, Any]:
        """Build retrieval context via embeddings and cosine similarity."""
        docs = self._extract_documents(knowledge_docs)
        self._backend.index_documents(docs)
        matches = self._backend.similarity_search(query=log_text, top_k=self._config.top_k)
        return {
            "query": log_text,
            "matches": matches,
        }

    def _extract_documents(self, knowledge_docs: Any) -> list[str]:
        """Extract textual entries from knowledge JSON."""
        if not knowledge_docs:
            return []
        if isinstance(knowledge_docs, str):
            lines = [line.strip() for line in knowledge_docs.splitlines() if line.strip()]
            return lines if lines else [knowledge_docs]
        if isinstance(knowledge_docs, dict) and "documents" in knowledge_docs and isinstance(knowledge_docs["documents"], list):
            return [str(item) for item in knowledge_docs["documents"]]
        return [str(knowledge_docs)]

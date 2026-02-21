"""FAISS cosine similarity backend with local sentence-transformers embeddings."""

from __future__ import annotations

from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.errors.exceptions import RetrievalError
from src.retrieval.embedding_backend import EmbeddingBackend


class FaissBackend(EmbeddingBackend):
    """FAISS-backed similarity index."""

    def __init__(self, model_name: str) -> None:
        """Initialize embedding model and index placeholders."""
        self._model = SentenceTransformer(model_name)
        self._index: faiss.IndexFlatIP | None = None
        self._documents: list[str] = []

    def _embed(self, texts: list[str]) -> np.ndarray:
        """Generate normalized embeddings."""
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype(np.float32)

    def index_documents(self, docs: list[str]) -> None:
        """Create cosine-similarity index."""
        self._documents = docs
        if not docs:
            self._index = None
            return
        vectors = self._embed(docs)
        self._index = faiss.IndexFlatIP(vectors.shape[1])
        self._index.add(vectors)

    def similarity_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Search indexed documents by cosine similarity."""
        if not self._documents or self._index is None:
            return []
        if top_k <= 0:
            raise RetrievalError("top_k must be > 0")
        query_vector = self._embed([query])
        scores, indices = self._index.search(query_vector, min(top_k, len(self._documents)))
        results: list[dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append({"score": float(score), "document": self._documents[int(idx)]})
        return results


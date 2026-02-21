"""Retrieval backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EmbeddingBackend(ABC):
    """Abstract retrieval backend contract."""

    @abstractmethod
    def index_documents(self, docs: list[str]) -> None:
        """Index documents for similarity search."""

    @abstractmethod
    def similarity_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Return top-k matches with scores."""


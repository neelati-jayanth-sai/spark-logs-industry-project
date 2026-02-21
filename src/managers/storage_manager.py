"""Storage manager layer."""

from __future__ import annotations

from typing import Any

from src.storage.s3_storage import S3Storage


class StorageManager:
    """Business-facing storage manager."""

    def __init__(self, storage: S3Storage) -> None:
        """Initialize with storage adapter."""
        self._storage = storage

    def fetch_logs(self, job_id: str, execution_id: str) -> str | None:
        """Fetch raw logs."""
        return self._storage.fetch_logs(job_id=job_id, execution_id=execution_id)

    def fetch_lineage(self, job_name: str) -> dict[str, Any] | None:
        """Fetch lineage payload."""
        return self._storage.fetch_lineage(job_name=job_name)

    def fetch_knowledge(self) -> dict[str, Any]:
        """Fetch knowledge payload."""
        return self._storage.fetch_knowledge()

    def fetch_solutions(self) -> dict[str, Any]:
        """Fetch solutions payload."""
        return self._storage.fetch_solutions()

    def fetch_severity_cases_excel(self) -> bytes | None:
        """Fetch severity case data Excel bytes."""
        return self._storage.fetch_severity_cases_excel()

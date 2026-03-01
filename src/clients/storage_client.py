"""Storage manager layer."""

from __future__ import annotations

from typing import Any

from storage.s3_storage import S3Storage


class StorageClient:
    """Business-facing storage manager."""

    def __init__(self, storage: S3Storage) -> None:
        """Initialize with storage adapter."""
        self._storage = storage

    def fetch_logs(self, job_id: str, run_id: str) -> str | None:
        """Fetch raw logs."""
        return self._storage.fetch_logs(job_id=job_id, run_id=run_id)

    def fetch_lineage(self, job_name: str) -> dict[str, Any] | None:
        """Fetch lineage payload."""
        return self._storage.fetch_lineage(job_name=job_name)

    def fetch_knowledge(self) -> str:
        """Fetch knowledge text payload."""
        return self._storage.fetch_knowledge()

    def fetch_solutions(self) -> str:
        """Fetch solutions text payload."""
        return self._storage.fetch_solutions()

    def fetch_severity_cases_csv(self) -> bytes | None:
        """Fetch severity case data CSV bytes."""
        return self._storage.fetch_severity_cases_csv()

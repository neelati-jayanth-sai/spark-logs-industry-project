"""Deterministic agent to fetch lineage data."""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseAgent
from src.schemas.models import AgentResult
from src.clients.storage_client import StorageClient
from src.state.rca_state import RCAState


class LineageAgent(BaseAgent):
    """Fetches lineage graph data from storage."""

    def __init__(self, storage_client: StorageClient) -> None:
        """Initialize dependencies."""
        super().__init__(name="lineage")
        self._storage_client = storage_client

    async def run(self, state: RCAState) -> dict[str, Any]:
        """Fetch lineage and return partial state update."""
        try:
            lineage = self._storage_client.fetch_lineage(state["job_name"]) or {}
            result = AgentResult(
                status="success",
                data={"lineage_found": bool(lineage)},
                confidence=1.0,
                meta={},
            )
            partial_update = {"lineage": lineage}
            return self._append_history(state, result, partial_state=partial_update)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to fetch lineage", error)
            return self._attach_error(state, wrapped)


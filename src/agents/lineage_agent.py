"""Deterministic agent to fetch lineage data."""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.domain.models import AgentResult
from src.managers.storage_manager import StorageManager
from src.state.rca_state import RCAState, RCAStateFactory


class LineageAgent(BaseAgent):
    """Fetches lineage graph data from storage."""

    def __init__(self, storage_manager: StorageManager) -> None:
        """Initialize dependencies."""
        super().__init__(name="lineage")
        self._storage_manager = storage_manager

    def run(self, state: RCAState) -> RCAState:
        """Fetch lineage and update state."""
        try:
            lineage = self._storage_manager.fetch_lineage(state["job_name"]) or {}
            result = AgentResult(
                status="success",
                data={"lineage_found": bool(lineage)},
                confidence=1.0,
                meta={},
            )
            updated = RCAStateFactory.clone_with_updates(state, {"lineage": lineage})
            return self._append_history(updated, result)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to fetch lineage", error)
            return self._attach_error(state, wrapped)


"""Deterministic agent to detect driver failure."""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseAgent
from src.schemas.models import AgentResult
from src.clients.iomete_client import IometeClient
from src.state.rca_state import RCAState


class DriverFailureAgent(BaseAgent):
    """Detects Spark driver-side failure through IOMETE API without LLM."""

    def __init__(self, iomete_client: IometeClient) -> None:
        """Initialize agent."""
        super().__init__(name="driver_failure")
        self._iomete_client = iomete_client

    async def run(self, state: RCAState) -> dict[str, Any]:
        """Detect driver failure deterministically and return partial state update."""
        try:
            self._logger.info(
                "driver_failure_check_started job_id=%s run_id=%s",
                state["job_id"],
                state["run_id"],
            )
            failure = self._iomete_client.detect_driver_failure(
                job_id=state["job_id"],
                run_id=state["run_id"],
            )
            self._logger.info(
                "driver_failure_check_completed job_id=%s run_id=%s driver_failure=%s",
                state["job_id"],
                state["run_id"],
                failure,
            )
            result = AgentResult(
                status="success",
                data={"driver_failure": failure},
                confidence=1.0,
                meta={},
            )
            partial_update = {"driver_failure": failure}
            return self._append_history(state, result, partial_state=partial_update)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to detect driver failure", error)
            return self._attach_error(state, wrapped)

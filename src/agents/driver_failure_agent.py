"""Deterministic agent to detect driver failure."""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.domain.models import AgentResult
from src.managers.iomete_manager import IometeManager
from src.state.rca_state import RCAState, RCAStateFactory


class DriverFailureAgent(BaseAgent):
    """Detects Spark driver-side failure through IOMETE API without LLM."""

    def __init__(self, iomete_manager: IometeManager) -> None:
        """Initialize agent."""
        super().__init__(name="driver_failure")
        self._iomete_manager = iomete_manager

    def run(self, state: RCAState) -> RCAState:
        """Detect driver failure deterministically."""
        try:
            self._logger.info(
                "driver_failure_check_started job_id=%s execution_id=%s",
                state["job_id"],
                state["execution_id"],
            )
            failure = self._iomete_manager.detect_driver_failure(
                job_id=state["job_id"],
                execution_id=state["execution_id"],
            )
            self._logger.info(
                "driver_failure_check_completed job_id=%s execution_id=%s driver_failure=%s",
                state["job_id"],
                state["execution_id"],
                failure,
            )
            result = AgentResult(
                status="success",
                data={"driver_failure": failure},
                confidence=1.0,
                meta={},
            )
            updated = RCAStateFactory.clone_with_updates(state, {"driver_failure": failure})
            return self._append_history(updated, result)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to detect driver failure", error)
            return self._attach_error(state, wrapped)

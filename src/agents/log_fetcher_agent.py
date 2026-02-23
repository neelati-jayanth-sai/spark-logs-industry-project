"""Deterministic agent to fetch logs."""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.domain.models import AgentResult
from src.managers.iomete_manager import IometeManager
from src.managers.splunk_manager import SplunkManager
from src.state.rca_state import RCAState, RCAStateFactory


class LogFetcherAgent(BaseAgent):
    """Fetches logs from IOMETE first, then Splunk fallback."""

    def __init__(self, iomete_manager: IometeManager, splunk_manager: SplunkManager) -> None:
        """Initialize dependencies."""
        super().__init__(name="log_fetcher")
        self._iomete_manager = iomete_manager
        self._splunk_manager = splunk_manager

    def run(self, state: RCAState) -> RCAState:
        """Fetch logs and update state."""
        try:
            self._logger.info(
                "log_fetch_started job_id=%s run_id=%s source_order=iomete_then_splunk",
                state["job_id"],
                state["run_id"],
            )
            logs = self._iomete_manager.fetch_logs(state["job_id"], state["run_id"])
            source = "iomete"
            if not logs:
                self._logger.info(
                    "iomete_logs_unavailable job_id=%s run_id=%s fallback=splunk",
                    state["job_id"],
                    state["run_id"],
                )
                logs = self._splunk_manager.fetch_logs(state["job_id"], state["run_id"])
                source = "splunk"
            logs = logs or ""
            result = AgentResult(
                status="success",
                data={"logs_found": bool(logs), "source": source if logs else "none"},
                confidence=1.0,
                meta={},
            )
            self._logger.info(
                "log_fetch_completed job_id=%s run_id=%s logs_found=%s source=%s persisted=%s",
                state["job_id"],
                state["run_id"],
                bool(logs),
                source if logs else "none",
                False,
            )
            updated = RCAStateFactory.clone_with_updates(
                state,
                {"logs": logs, "log_source": source if logs else "none"},
            )
            return self._append_history(updated, result)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to fetch logs", error)
            return self._attach_error(state, wrapped)

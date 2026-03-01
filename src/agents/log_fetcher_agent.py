"""Deterministic agent to fetch logs."""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseAgent
from src.schemas.models import AgentResult
from src.clients.iomete_client import IometeClient
from src.clients.splunk_client import SplunkClient
from src.state.rca_state import RCAState


class LogFetcherAgent(BaseAgent):
    """Fetches logs from IOMETE first, then Splunk fallback."""

    def __init__(self, iomete_client: IometeClient, splunk_client: SplunkClient) -> None:
        """Initialize dependencies."""
        super().__init__(name="log_fetcher")
        self._iomete_client = iomete_client
        self._splunk_client = splunk_client

    async def run(self, state: RCAState) -> dict[str, Any]:
        """Fetch logs and return partial state update."""
        try:
            self._logger.info(
                "log_fetch_started job_id=%s run_id=%s source_order=iomete_then_splunk",
                state["job_id"],
                state["run_id"],
            )
            logs = self._iomete_client.fetch_logs(state["job_id"], state["run_id"])
            source = "iomete"
            if not logs:
                self._logger.info(
                    "iomete_logs_unavailable job_id=%s run_id=%s fallback=splunk",
                    state["job_id"],
                    state["run_id"],
                )
                logs = self._splunk_client.fetch_logs(state["job_id"], state["run_id"])
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
            partial_update = {
                "logs": logs, 
                "log_source": source if logs else "none"
            }
            return self._append_history(state, result, partial_state=partial_update)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to fetch logs", error)
            return self._attach_error(state, wrapped)

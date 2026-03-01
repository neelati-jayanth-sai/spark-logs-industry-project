"""RCA engine entrypoint."""

from __future__ import annotations

import logging
from typing import Any

from src.errors.exceptions import GraphError
from src.state.rca_state import RCAState, RCAStateValidator
from src.utils.time_utils import TimeUtils


class RCAEngine:
    """Entry controller for the RCA runtime."""

    def __init__(self, graph_builder: Any, callbacks: list[Any] | None = None) -> None:
        """Initialize engine dependencies."""
        self._graph_builder = graph_builder
        self._callbacks = callbacks or []
        self._logger = logging.getLogger("src.system.engine")

    def run(self, job_id: str, job_name: str, run_id: str) -> RCAState:
        """Create state, execute graph, and return terminal state."""
        self._logger.info(
            "engine_run_started job_id=%s job_name=%s run_id=%s",
            job_id,
            job_name,
            run_id,
        )
        start_time = TimeUtils.utc_now_iso()
        state: dict[str, Any] = {
            "job_id": job_id,
            "job_name": job_name,
            "run_id": run_id,
            "start_time": start_time,
            "logs": "",
            "summary": "",
            "root_cause": "",
            "solution": "",
            "category": "",
            "lineage": {},
            "end_time": "",
            "status": "running",
            "errors": [],
            "decision_path": [],
            "agent_history": [],
            "confidence_scores": {},
            "driver_failure": False,
            "retrieval_context": {},
            "log_source": "none",
            "error_type": "",
            "error_message": "",
            "severity": "",
            "resolution": [],
            "solution_source": "",
        }
        RCAStateValidator.validate(state)
        try:
            graph = self._graph_builder.build()
            final_state: dict[str, Any] = graph.invoke(state, config={"callbacks": self._callbacks})
            
            # Final state updates
            completed = dict(final_state)
            completed["end_time"] = TimeUtils.utc_now_iso()
            completed["status"] = "completed" if not completed.get("errors") else "failed"
            RCAStateValidator.validate(completed)
            self._logger.info(
                "engine_run_completed job_id=%s run_id=%s status=%s errors=%s",
                job_id,
                run_id,
                completed["status"],
                len(completed["errors"]),
            )
            return completed
        except Exception as error:  # noqa: BLE001
            failed = dict(state)
            failed["end_time"] = TimeUtils.utc_now_iso()
            failed["status"] = "failed"
            failed_error = {"code": "GraphError", "message": str(error), "source": "engine", "details": {}}
            failed["errors"] = failed.get("errors", []) + [failed_error]
            RCAStateValidator.validate(failed)
            self._logger.exception(
                "engine_run_failed job_id=%s run_id=%s error=%s",
                job_id,
                run_id,
                error,
            )
            raise GraphError(f"RCA engine execution failed: {error}") from error

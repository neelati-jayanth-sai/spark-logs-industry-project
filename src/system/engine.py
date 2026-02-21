"""RCA engine entrypoint."""

from __future__ import annotations

import logging
from typing import Any

from src.errors.exceptions import GraphError
from src.state.rca_state import RCAState, RCAStateFactory, RCAStateValidator
from src.utils.time_utils import TimeUtils


class RCAEngine:
    """Entry controller for the RCA runtime."""

    def __init__(self, graph_builder: Any, callbacks: list[Any] | None = None) -> None:
        """Initialize engine dependencies."""
        self._graph_builder = graph_builder
        self._callbacks = callbacks or []
        self._logger = logging.getLogger("src.system.engine")

    def run(self, job_id: str, job_name: str, execution_id: str) -> RCAState:
        """Create state, execute graph, and return terminal state."""
        self._logger.info(
            "engine_run_started job_id=%s job_name=%s execution_id=%s",
            job_id,
            job_name,
            execution_id,
        )
        start_time = TimeUtils.utc_now_iso()
        state = RCAStateFactory.create_initial(
            job_id=job_id,
            job_name=job_name,
            execution_id=execution_id,
            start_time=start_time,
        )
        RCAStateValidator.validate(state)
        try:
            graph = self._graph_builder.build()
            final_state: RCAState = graph.invoke(state, config={"callbacks": self._callbacks})
            completed = RCAStateFactory.clone_with_updates(
                final_state,
                {"end_time": TimeUtils.utc_now_iso(), "status": "completed" if not final_state["errors"] else "failed"},
            )
            RCAStateValidator.validate(completed)
            self._logger.info(
                "engine_run_completed job_id=%s execution_id=%s status=%s errors=%s",
                job_id,
                execution_id,
                completed["status"],
                len(completed["errors"]),
            )
            return completed
        except Exception as error:  # noqa: BLE001
            failed = RCAStateFactory.clone_with_updates(
                state,
                {
                    "end_time": TimeUtils.utc_now_iso(),
                    "status": "failed",
                    "errors": [*state["errors"], {"code": "GraphError", "message": str(error), "source": "engine", "details": {}}],
                },
            )
            RCAStateValidator.validate(failed)
            self._logger.exception(
                "engine_run_failed job_id=%s execution_id=%s error=%s",
                job_id,
                execution_id,
                error,
            )
            raise GraphError(f"RCA engine execution failed: {error}") from error

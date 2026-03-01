"""Graph state schema and validation helpers."""

from __future__ import annotations

import json
import operator
from typing import Annotated, Any, TypedDict


class RCAState(TypedDict):
    """Single source of truth partial state object used by the graph."""

    job_id: str
    job_name: str
    logs: str
    summary: str
    root_cause: str
    solution: str
    category: str
    lineage: dict[str, Any]
    run_id: str
    start_time: str
    end_time: str
    status: str
    errors: Annotated[list[dict[str, Any]], operator.add]
    decision_path: Annotated[list[str], operator.add]
    agent_history: Annotated[list[dict[str, Any]], operator.add]
    confidence_scores: dict[str, float]
    driver_failure: bool
    retrieval_context: dict[str, Any]
    log_source: str
    error_type: str
    error_message: str
    severity: str
    resolution: list[str]
    solution_source: str


class RCAStateValidator:
    """State validation checks."""

    _required_keys: tuple[str, ...] = (
        "job_id",
        "job_name",
        "logs",
        "summary",
        "root_cause",
        "solution",
        "category",
        "lineage",
        "run_id",
        "start_time",
        "end_time",
        "status",
        "errors",
        "decision_path",
        "agent_history",
        "confidence_scores",
        "driver_failure",
        "retrieval_context",
        "log_source",
        "error_type",
        "error_message",
        "severity",
        "resolution",
        "solution_source",
    )

    @classmethod
    def validate(cls, state: dict[str, Any] | RCAState) -> None:
        """Validate required keys."""
        missing = [key for key in cls._required_keys if key not in state]
        if missing:
            raise ValueError(f"State missing required keys: {missing}")
        # Note: json dumps check removed here for performance. Use graph debug logs instead.

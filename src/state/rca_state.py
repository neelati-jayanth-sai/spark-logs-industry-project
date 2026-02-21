"""Graph state schema and validation helpers."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, TypedDict


class RCAState(TypedDict):
    """Single source of truth state object used by the graph."""

    job_id: str
    job_name: str
    logs: str
    summary: str
    root_cause: str
    solution: str
    category: str
    lineage: dict[str, Any]
    execution_id: str
    start_time: str
    end_time: str
    status: str
    errors: list[dict[str, Any]]
    decision_path: list[str]
    agent_history: list[dict[str, Any]]
    confidence_scores: dict[str, float]
    driver_failure: bool
    retrieval_context: dict[str, Any]
    log_source: str
    error_type: str
    error_message: str
    severity: str
    resolution: list[str]
    solution_source: str


class RCAStateFactory:
    """Factory and immutable update helpers for RCA state."""

    @classmethod
    def create_initial(cls, job_id: str, job_name: str, execution_id: str, start_time: str) -> RCAState:
        """Create initial graph state."""
        return RCAState(
            job_id=job_id,
            job_name=job_name,
            logs="",
            summary="",
            root_cause="",
            solution="",
            category="",
            lineage={},
            execution_id=execution_id,
            start_time=start_time,
            end_time="",
            status="running",
            errors=[],
            decision_path=[],
            agent_history=[],
            confidence_scores={},
            driver_failure=False,
            retrieval_context={},
            log_source="none",
            error_type="",
            error_message="",
            severity="",
            resolution=[],
            solution_source="",
        )

    @classmethod
    def clone_with_updates(cls, state: RCAState, updates: dict[str, Any]) -> RCAState:
        """Return an updated state copy."""
        copied: dict[str, Any] = deepcopy(state)
        copied.update(updates)
        return RCAState(**copied)


class RCAStateValidator:
    """State validation and JSON-safety checks."""

    _required_keys: tuple[str, ...] = (
        "job_id",
        "job_name",
        "logs",
        "summary",
        "root_cause",
        "solution",
        "category",
        "lineage",
        "execution_id",
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
    def validate(cls, state: RCAState) -> None:
        """Validate required keys and JSON serializability."""
        missing = [key for key in cls._required_keys if key not in state]
        if missing:
            raise ValueError(f"State missing required keys: {missing}")
        json.dumps(state)

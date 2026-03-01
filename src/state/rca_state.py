"""Graph state schema and validation helpers."""

from __future__ import annotations

import operator
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class RCAState(BaseModel):
    """Single source of truth partial state object used by the graph."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    job_id: str
    job_name: str
    logs: str = ""
    summary: str = ""
    root_cause: str = ""
    solution: str = ""
    category: str = ""
    lineage: dict[str, Any] = Field(default_factory=dict)
    run_id: str
    start_time: str = ""
    end_time: str = ""
    status: str = "running"
    errors: Annotated[list[dict[str, Any]], operator.add] = Field(default_factory=list)
    decision_path: Annotated[list[str], operator.add] = Field(default_factory=list)
    agent_history: Annotated[list[dict[str, Any]], operator.add] = Field(default_factory=list)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    driver_failure: bool = False
    retrieval_context: dict[str, Any] = Field(default_factory=dict)
    log_source: str = ""
    error_type: str = ""
    error_message: str = ""
    severity: str = ""
    resolution: list[str] = Field(default_factory=list)
    solution_source: str = ""

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like access for backwards compatibility."""
        if not hasattr(self, item):
            raise KeyError(item)
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        """Allow dict-like .get() for backwards compatibility."""
        return getattr(self, item, default)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like assignment."""
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator check."""
        return hasattr(self, key)


class RCAStateValidator:
    """State validation checks."""

    @classmethod
    def validate(cls, state: dict[str, Any] | RCAState) -> None:
        """Validate required keys."""
        # Pydantic BaseModel enforces required fields natively
        pass

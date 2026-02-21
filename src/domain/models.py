"""Domain models for RCA platform."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentResult:
    """Canonical structured output envelope for all agents."""

    status: str
    data: dict[str, Any]
    confidence: float
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class LogPayload:
    """Payload for fetched logs."""

    content: str


@dataclass(frozen=True)
class LineagePayload:
    """Payload for lineage graph data."""

    lineage: dict[str, Any]


@dataclass(frozen=True)
class CategoryPayload:
    """Payload for RCA category classification."""

    category: str


@dataclass(frozen=True)
class RootCausePayload:
    """Payload for inferred root cause."""

    root_cause: str


@dataclass(frozen=True)
class SolutionPayload:
    """Payload for generated solution."""

    solution: str


@dataclass(frozen=True)
class ErrorEntry:
    """Typed error entry persisted in state."""

    code: str
    message: str
    source: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation for state serialization."""
        return asdict(self)


@dataclass(frozen=True)
class FailedJob:
    """Failed job descriptor from IOMETE."""

    job_id: str
    job_name: str


@dataclass(frozen=True)
class FailedExecution:
    """Failed execution descriptor for a job."""

    execution_id: str

"""Base agent class."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from schemas.models import AgentResult, ErrorEntry
from errors.exceptions import AgentError
from state.rca_state import RCAState


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str) -> None:
        """Initialize base agent."""
        self._name = name
        self._logger = logging.getLogger(f"src.agents.{name}")

    @abstractmethod
    async def run(self, state: RCAState) -> dict[str, Any]:
        """Execute agent logic and return partial updated state."""

    def _append_history(self, state: RCAState, result: AgentResult, partial_state: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return partial state updates with agent output metadata."""
        updates: dict[str, Any] = partial_state or {}
        
        self._logger.info(
            "agent_completed name=%s status=%s confidence=%.3f",
            self._name,
            result.status,
            result.confidence,
        )
        
        scores = dict(state.get("confidence_scores", {}))
        scores[self._name] = result.confidence
        
        updates.update({
            "agent_history": [{"agent": self._name, "result": result.to_dict()}],
            "decision_path": [self._name],
            "confidence_scores": scores,
        })
        return updates

    def _attach_error(self, state: RCAState, error: Exception) -> dict[str, Any]:
        """Return partial state update with typed error entry and failure status."""
        self._logger.exception("agent_failed name=%s error=%s", self._name, error)
        entry = ErrorEntry(
            code=error.__class__.__name__,
            message=str(error),
            source=self._name,
            details={},
        )
        return {
            "errors": [entry.to_dict()], 
            "status": "failed"
        }

    def _wrap_exception(self, message: str, error: Exception) -> AgentError:
        """Wrap generic exceptions into typed agent error."""
        return AgentError(f"{self._name}: {message}: {error}")

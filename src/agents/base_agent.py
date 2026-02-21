"""Base agent class."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from src.domain.models import AgentResult, ErrorEntry
from src.errors.exceptions import AgentError
from src.state.rca_state import RCAState, RCAStateFactory


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, name: str) -> None:
        """Initialize base agent."""
        self._name = name
        self._logger = logging.getLogger(f"src.agents.{name}")

    @abstractmethod
    def run(self, state: RCAState) -> RCAState:
        """Execute agent logic and return updated state."""

    def _append_history(self, state: RCAState, result: AgentResult) -> RCAState:
        """Append agent output metadata to state history."""
        self._logger.info(
            "agent_completed name=%s status=%s confidence=%.3f",
            self._name,
            result.status,
            result.confidence,
        )
        history = [*state["agent_history"], {"agent": self._name, "result": result.to_dict()}]
        scores = dict(state["confidence_scores"])
        scores[self._name] = result.confidence
        decision_path = [*state["decision_path"], self._name]
        return RCAStateFactory.clone_with_updates(
            state,
            {"agent_history": history, "confidence_scores": scores, "decision_path": decision_path},
        )

    def _attach_error(self, state: RCAState, error: Exception) -> RCAState:
        """Attach typed error entry to state."""
        self._logger.exception("agent_failed name=%s error=%s", self._name, error)
        entry = ErrorEntry(
            code=error.__class__.__name__,
            message=str(error),
            source=self._name,
            details={},
        )
        errors = [*state["errors"], entry.to_dict()]
        return RCAStateFactory.clone_with_updates(state, {"errors": errors, "status": "failed"})

    def _wrap_exception(self, message: str, error: Exception) -> AgentError:
        """Wrap generic exceptions into typed agent error."""
        return AgentError(f"{self._name}: {message}: {error}")

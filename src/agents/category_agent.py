"""Reasoning agent for category classification."""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.llm.structured_output import StructuredAgentOutput
from src.managers.llm_manager import LLMManager
from src.state.rca_state import RCAState, RCAStateFactory


class CategoryAgent(BaseAgent):
    """Classifies failure category."""

    def __init__(self, llm_manager: LLMManager) -> None:
        """Initialize dependencies."""
        super().__init__(name="category")
        self._llm_manager = llm_manager

    def run(self, state: RCAState) -> RCAState:
        """Generate category from summary/root cause."""
        try:
            result = self._llm_manager.invoke_structured(
                prompt_key="category",
                input_payload={"summary": state["summary"], "root_cause": state["root_cause"]},
                output_schema=StructuredAgentOutput,
            )
            category = str(result.data.get("category", ""))
            updated = RCAStateFactory.clone_with_updates(state, {"category": category})
            return self._append_history(updated, result)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to classify category", error)
            return self._attach_error(state, wrapped)


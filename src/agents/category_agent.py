"""Reasoning agent for category classification."""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseAgent
from src.llm.structured_output import StructuredAgentOutput
from src.clients.llm_client import LLMClient
from src.state.rca_state import RCAState


class CategoryAgent(BaseAgent):
    """Classifies failure category."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize dependencies."""
        super().__init__(name="category")
        self._llm_client = llm_client

    async def run(self, state: RCAState) -> dict[str, Any]:
        """Generate category from summary/root cause and return partial state update."""
        try:
            result = await self._llm_client.ainvoke_structured(
                prompt_key="category",
                input_payload={"summary": state["summary"], "root_cause": state["root_cause"]},
                output_schema=StructuredAgentOutput,
            )
            category = str(result.data.get("category", ""))
            partial_update = {"category": category}
            return self._append_history(state, result, partial_state=partial_update)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to classify category", error)
            return self._attach_error(state, wrapped)


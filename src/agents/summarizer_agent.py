"""Reasoning agent for log summarization."""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseAgent
from src.llm.structured_output import StructuredAgentOutput
from src.managers.llm_manager import LLMManager
from src.managers.retrieval_manager import RetrievalManager
from src.managers.storage_manager import StorageManager
from src.state.rca_state import RCAState


class SummarizerAgent(BaseAgent):
    """Summarizes logs with retrieval-grounded context."""

    def __init__(
        self, llm_manager: LLMManager, retrieval_manager: RetrievalManager, storage_manager: StorageManager
    ) -> None:
        """Initialize dependencies."""
        super().__init__(name="summarizer")
        self._llm_manager = llm_manager
        self._retrieval_manager = retrieval_manager
        self._storage_manager = storage_manager

    def run(self, state: RCAState) -> dict[str, Any]:
        """Summarize logs and return partial state update."""
        try:
            knowledge = self._storage_manager.fetch_knowledge()
            context = self._retrieval_manager.build_context(state["logs"], knowledge)
            result = self._llm_manager.invoke_structured(
                prompt_key="summarizer",
                input_payload={"logs": state["logs"], "context": context},
                output_schema=StructuredAgentOutput,
            )
            summary = str(result.data.get("summary", ""))
            error_type = str(result.data.get("error_type", ""))
            error_message = str(result.data.get("error_message", ""))
            
            partial_update = {
                "summary": summary,
                "error_type": error_type,
                "error_message": error_message,
                "retrieval_context": context,
            }
            return self._append_history(state, result, partial_state=partial_update)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to summarize logs", error)
            return self._attach_error(state, wrapped)

"""Reasoning agent for root cause inference."""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.llm.structured_output import StructuredAgentOutput
from src.managers.llm_manager import LLMManager
from src.managers.retrieval_manager import RetrievalManager
from src.managers.storage_manager import StorageManager
from src.state.rca_state import RCAState, RCAStateFactory


class RCAAgent(BaseAgent):
    """Infers root cause from state context."""

    def __init__(
        self, llm_manager: LLMManager, retrieval_manager: RetrievalManager, storage_manager: StorageManager
    ) -> None:
        """Initialize dependencies."""
        super().__init__(name="rca")
        self._llm_manager = llm_manager
        self._retrieval_manager = retrieval_manager
        self._storage_manager = storage_manager

    def run(self, state: RCAState) -> RCAState:
        """Infer root cause via structured LLM output."""
        try:
            context = state["retrieval_context"]
            if not context and state["logs"]:
                knowledge = self._storage_manager.fetch_knowledge()
                context = self._retrieval_manager.build_context(state["logs"], knowledge)
            result = self._llm_manager.invoke_structured(
                prompt_key="rca",
                input_payload={
                    "logs": state["logs"],
                    "summary": state["summary"],
                    "error_type": state["error_type"],
                    "error_message": state["error_message"],
                    "category": state["category"],
                    "lineage": state["lineage"],
                    "context": context,
                },
                output_schema=StructuredAgentOutput,
            )
            root_cause = str(result.data.get("root_cause", ""))
            rca_category = str(result.data.get("rca_category", state["category"]))
            updated = RCAStateFactory.clone_with_updates(
                state,
                {
                    "root_cause": root_cause,
                    "category": rca_category,
                    "retrieval_context": context,
                },
            )
            return self._append_history(updated, result)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to infer root cause", error)
            return self._attach_error(state, wrapped)

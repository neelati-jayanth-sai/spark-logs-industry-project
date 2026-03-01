"""Reasoning agent for root cause inference."""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseAgent
from src.llm.structured_output import StructuredAgentOutput
from src.clients.llm_client import LLMClient
from src.clients.retrieval_client import RetrievalClient
from src.clients.storage_client import StorageClient
from src.state.rca_state import RCAState


class RCAAgent(BaseAgent):
    """Infers root cause from state context."""

    def __init__(
        self, llm_client: LLMClient, retrieval_client: RetrievalClient, storage_client: StorageClient
    ) -> None:
        """Initialize dependencies."""
        super().__init__(name="rca")
        self._llm_client = llm_client
        self._retrieval_client = retrieval_client
        self._storage_client = storage_client

    async def run(self, state: RCAState) -> dict[str, Any]:
        """Infer root cause via structured LLM output and return partial state update."""
        try:
            context = state.get("retrieval_context", {})
            if not context and state.get("logs"):
                knowledge = self._storage_client.fetch_knowledge()
                context = self._retrieval_client.build_context(state["logs"], knowledge)
            result = await self._llm_client.ainvoke_structured(
                prompt_key="rca",
                input_payload={
                    "logs": state.get("logs", ""),
                    "summary": state.get("summary", ""),
                    "error_type": state.get("error_type", ""),
                    "error_message": state.get("error_message", ""),
                    "category": state.get("category", ""),
                    "lineage": state.get("lineage", {}),
                    "context": context,
                },
                output_schema=StructuredAgentOutput,
            )
            root_cause = str(result.data.get("root_cause", ""))
            rca_category = str(result.data.get("rca_category", state.get("category", "")))
            
            partial_update = {
                "root_cause": root_cause,
                "category": rca_category,
                "retrieval_context": context,
            }
            return self._append_history(state, result, partial_state=partial_update)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to infer root cause", error)
            return self._attach_error(state, wrapped)

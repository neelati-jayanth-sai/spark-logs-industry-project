"""Reasoning agent for log summarization."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent
from llm.structured_output import StructuredAgentOutput
from clients.llm_client import LLMClient
from clients.retrieval_client import RetrievalClient
from clients.storage_client import StorageClient
from state.rca_state import RCAState


class SummarizerAgent(BaseAgent):
    """Summarizes logs with retrieval-grounded context."""

    def __init__(
        self, llm_client: LLMClient, retrieval_client: RetrievalClient, storage_client: StorageClient
    ) -> None:
        """Initialize dependencies."""
        super().__init__(name="summarizer")
        self._llm_client = llm_client
        self._retrieval_client = retrieval_client
        self._storage_client = storage_client

    async def run(self, state: RCAState) -> dict[str, Any]:
        """Summarize logs and return partial state update."""
        try:
            knowledge = self._storage_client.fetch_knowledge()
            context = self._retrieval_client.build_context(state["logs"], knowledge)
            result = await self._llm_client.ainvoke_structured(
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

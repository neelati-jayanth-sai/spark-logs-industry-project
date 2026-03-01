"""Reasoning agent for solution generation."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent
from llm.structured_output import StructuredAgentOutput
from clients.llm_client import LLMClient
from clients.severity_client import SeverityClient
from clients.storage_client import StorageClient
from state.rca_state import RCAState


class SolutionAgent(BaseAgent):
    """Generates remediation guidance."""

    def __init__(
        self,
        llm_client: LLMClient,
        storage_client: StorageClient,
        severity_client: SeverityClient,
    ) -> None:
        """Initialize dependencies."""
        super().__init__(name="solution")
        self._llm_client = llm_client
        self._storage_client = storage_client
        self._severity_client = severity_client

    async def run(self, state: RCAState) -> dict[str, Any]:
        """Generate solution via structured LLM output and return partial update."""
        try:
            solutions = self._storage_client.fetch_solutions()
            result = await self._llm_client.ainvoke_structured(
                prompt_key="solution",
                input_payload={
                    "error_type": state.get("error_type", ""),
                    "error_message": state.get("error_message", ""),
                    "root_cause": state.get("root_cause", ""),
                    "category": state.get("category", ""),
                    "solutions": solutions,
                },
                output_schema=StructuredAgentOutput,
            )
            solution = str(result.data.get("solution", ""))
            severity, case_count = self._severity_client.classify_severity(
                error_type=state.get("error_type", ""),
                error_message=state.get("error_message", ""),
                root_cause=state.get("root_cause", ""),
            )
            resolution_raw = result.data.get("resolution", [])
            resolution = [str(item) for item in resolution_raw] if isinstance(resolution_raw, list) else [str(solution)]
            solution_source = str(result.data.get("source", "knowledge_base"))
            
            partial_update = {
                "solution": solution,
                "severity": severity,
                "resolution": resolution,
                "solution_source": solution_source,
            }
            result.meta["severity_case_count"] = case_count
            return self._append_history(state, result, partial_state=partial_update)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to generate solution", error)
            return self._attach_error(state, wrapped)

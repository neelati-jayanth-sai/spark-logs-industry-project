"""Reasoning agent for solution generation."""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.llm.structured_output import StructuredAgentOutput
from src.managers.llm_manager import LLMManager
from src.managers.severity_manager import SeverityManager
from src.managers.storage_manager import StorageManager
from src.state.rca_state import RCAState, RCAStateFactory


class SolutionAgent(BaseAgent):
    """Generates remediation guidance."""

    def __init__(
        self,
        llm_manager: LLMManager,
        storage_manager: StorageManager,
        severity_manager: SeverityManager,
    ) -> None:
        """Initialize dependencies."""
        super().__init__(name="solution")
        self._llm_manager = llm_manager
        self._storage_manager = storage_manager
        self._severity_manager = severity_manager

    def run(self, state: RCAState) -> RCAState:
        """Generate solution via structured LLM output."""
        try:
            solutions = self._storage_manager.fetch_solutions()
            result = self._llm_manager.invoke_structured(
                prompt_key="solution",
                input_payload={
                    "error_type": state["error_type"],
                    "error_message": state["error_message"],
                    "root_cause": state["root_cause"],
                    "category": state["category"],
                    "solutions": solutions,
                },
                output_schema=StructuredAgentOutput,
            )
            solution = str(result.data.get("solution", ""))
            severity, case_count = self._severity_manager.classify_severity(
                error_type=state["error_type"],
                error_message=state["error_message"],
                root_cause=state["root_cause"],
            )
            resolution_raw = result.data.get("resolution", [])
            resolution = [str(item) for item in resolution_raw] if isinstance(resolution_raw, list) else [str(solution)]
            solution_source = str(result.data.get("source", "knowledge_base"))
            updated = RCAStateFactory.clone_with_updates(
                state,
                {
                    "solution": solution,
                    "severity": severity,
                    "resolution": resolution,
                    "solution_source": solution_source,
                },
            )
            result.meta["severity_case_count"] = case_count
            return self._append_history(updated, result)
        except Exception as error:  # noqa: BLE001
            wrapped = self._wrap_exception("failed to generate solution", error)
            return self._attach_error(state, wrapped)

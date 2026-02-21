"""Integration tests for full graph execution with mocks."""

from src.agents.category_agent import CategoryAgent
from src.agents.driver_failure_agent import DriverFailureAgent
from src.agents.lineage_agent import LineageAgent
from src.agents.log_fetcher_agent import LogFetcherAgent
from src.agents.rca_agent import RCAAgent
from src.agents.solution_agent import SolutionAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.graph.rca_graph import RCAGraphBuilder
from src.state.rca_state import RCAStateFactory


class _StorageStub:
    """Storage stub for integration tests."""

    def fetch_logs(self, job_id: str, execution_id: str) -> str:
        return "executor heartbeat timed out"

    def fetch_lineage(self, job_name: str) -> dict:
        return {"parents": ["job_x"]}

    def fetch_knowledge(self) -> dict:
        return {"documents": ["heartbeat timeout usually indicates driver or network pressure"]}

    def fetch_solutions(self) -> dict:
        return {"documents": ["increase driver memory and inspect cluster network"]}


class _RetrievalStub:
    """Retrieval stub."""

    def build_context(self, log_text: str, knowledge_docs: dict) -> dict:
        return {"matches": [{"score": 0.99, "document": "context"}]}


class _LLMStub:
    """LLM stub returning structured envelopes."""

    def invoke_structured(self, prompt_key: str, input_payload: dict, output_schema: type) -> object:
        mapping = {
            "summarizer": {"summary": "heartbeat timeout detected"},
            "category": {"category": "driver_failure"},
            "rca": {"root_cause": "driver resource saturation"},
            "solution": {"solution": "increase driver memory"},
        }
        class _Result:
            status = "success"
            confidence = 0.9
            meta = {"prompt_key": prompt_key}
            data = mapping[prompt_key]
        return _Result()


class _IometeStub:
    """IOMETE detection stub."""

    def detect_driver_failure(self, job_id: str, execution_id: str) -> bool:
        return False

    def fetch_logs(self, job_id: str, execution_id: str) -> str:
        return "executor heartbeat timed out"


class _SplunkStub:
    """Splunk logs stub."""

    def fetch_logs(self, job_id: str, execution_id: str) -> str:
        return ""


class _SeverityStub:
    """Severity stub."""

    def classify_severity(self, error_type: str, error_message: str, root_cause: str) -> tuple[str, int]:
        return "high", 7


class TestGraphIntegration:
    """Graph execution paths."""

    def test_end_to_end_with_logs(self) -> None:
        """Graph should execute full path and produce solution."""
        storage = _StorageStub()
        retrieval = _RetrievalStub()
        llm = _LLMStub()

        builder = RCAGraphBuilder(
            log_fetcher_agent=LogFetcherAgent(_IometeStub(), _SplunkStub()),  # type: ignore[arg-type]
            driver_failure_agent=DriverFailureAgent(_IometeStub()),  # type: ignore[arg-type]
            lineage_agent=LineageAgent(storage),  # type: ignore[arg-type]
            summarizer_agent=SummarizerAgent(llm, retrieval, storage),  # type: ignore[arg-type]
            category_agent=CategoryAgent(llm),  # type: ignore[arg-type]
            rca_agent=RCAAgent(llm, retrieval, storage),  # type: ignore[arg-type]
            solution_agent=SolutionAgent(llm, storage, _SeverityStub()),  # type: ignore[arg-type]
        )
        graph = builder.build()
        state = RCAStateFactory.create_initial("j", "n", "e", "t")
        out = graph.invoke(state)
        assert out["root_cause"] == "driver resource saturation"
        assert out["solution"] == "increase driver memory"

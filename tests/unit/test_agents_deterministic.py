"""Unit tests for deterministic agents."""

from src.agents.driver_failure_agent import DriverFailureAgent
from src.agents.log_fetcher_agent import LogFetcherAgent
from src.agents.lineage_agent import LineageAgent
from src.state.rca_state import RCAStateFactory


class _StorageStub:
    """Storage stub for deterministic tests."""

    def fetch_logs(self, job_id: str, execution_id: str) -> str:
        return "driver crashed due to sparkcontext was shut down"

    def fetch_lineage(self, job_name: str) -> dict:
        return {"upstream": ["table_a"]}


class _IometeStub:
    """IOMETE API stub for deterministic tests."""

    def detect_driver_failure(self, job_id: str, execution_id: str) -> bool:
        return True

    def fetch_logs(self, job_id: str, execution_id: str) -> str:
        return "driver crashed from iomete"


class _SplunkStub:
    """Splunk API stub."""

    def fetch_logs(self, job_id: str, execution_id: str) -> str:
        return "driver crashed from splunk"


class TestDeterministicAgents:
    """Deterministic agent contract tests."""

    def test_log_fetcher(self) -> None:
        """Log fetcher should populate logs and structured history."""
        state = RCAStateFactory.create_initial("j", "n", "e", "t")
        agent = LogFetcherAgent(_IometeStub(), _SplunkStub())  # type: ignore[arg-type]
        updated = agent.run(state)
        assert updated["logs"]
        assert updated["agent_history"][-1]["result"]["status"] == "success"

    def test_driver_failure(self) -> None:
        """Driver failure agent should use iomete API response."""
        state = RCAStateFactory.create_initial("j", "n", "e", "t")
        agent = DriverFailureAgent(_IometeStub())  # type: ignore[arg-type]
        updated = agent.run(state)
        assert updated["driver_failure"] is True

    def test_lineage(self) -> None:
        """Lineage agent should populate lineage state."""
        state = RCAStateFactory.create_initial("j", "n", "e", "t")
        agent = LineageAgent(_StorageStub())  # type: ignore[arg-type]
        updated = agent.run(state)
        assert updated["lineage"]["upstream"] == ["table_a"]

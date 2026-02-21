"""Mock coverage tests for storage and llm contracts."""

from src.domain.models import AgentResult


class TestMockContracts:
    """Contract checks for mocks."""

    def test_agent_result_shape(self) -> None:
        """AgentResult must follow strict structured envelope."""
        result = AgentResult(status="success", data={"k": "v"}, confidence=1.0, meta={})
        payload = result.to_dict()
        assert set(payload.keys()) == {"status", "data", "confidence", "meta"}


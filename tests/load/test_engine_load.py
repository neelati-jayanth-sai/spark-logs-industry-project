"""Load-style tests for engine repeatability."""

from src.system.engine import RCAEngine


class _GraphBuilderStub:
    """Compiled graph stub."""

    class _Compiled:
        def invoke(self, state: dict, config: dict | None = None) -> dict:
            state["status"] = "completed"
            return state

    def build(self) -> "_GraphBuilderStub._Compiled":
        return self._Compiled()


class TestEngineLoad:
    """Repeated-run invariants."""

    def test_repeated_runs_no_state_bleed(self) -> None:
        """Each run should have isolated state."""
        engine = RCAEngine(graph_builder=_GraphBuilderStub(), callbacks=[])
        first = engine.run("j1", "n1", "e1")
        second = engine.run("j2", "n2", "e2")
        assert first["job_id"] == "j1"
        assert second["job_id"] == "j2"


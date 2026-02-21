"""Unit tests for graph routing logic."""

from src.graph.rca_graph import RCAGraphBuilder
from src.state.rca_state import RCAStateFactory


class TestRoutingRules:
    """Routing determinism tests."""

    def test_rule_a_logs_branch(self) -> None:
        """Logs should route to summarizer."""
        state = RCAStateFactory.create_initial("j", "n", "e", "t")
        state["logs"] = "some logs"
        assert RCAGraphBuilder._route_after_log_fetcher(state) == "summarizer"

    def test_rule_b_driver_shortcut(self) -> None:
        """Missing logs and driver failure should route directly to rca."""
        state = RCAStateFactory.create_initial("j", "n", "e", "t")
        state["logs"] = ""
        state["driver_failure"] = True
        assert RCAGraphBuilder._route_after_driver_failure(state) == "rca"

    def test_rule_c_category_branch(self) -> None:
        """Missing category should route to category node."""
        state = RCAStateFactory.create_initial("j", "n", "e", "t")
        state["category"] = ""
        assert RCAGraphBuilder._route_after_lineage(state) == "category"


"""RCA execution graph built with LangGraph StateGraph."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from src.agents.category_agent import CategoryAgent
from src.agents.driver_failure_agent import DriverFailureAgent
from src.agents.lineage_agent import LineageAgent
from src.agents.log_fetcher_agent import LogFetcherAgent
from src.agents.rca_agent import RCAAgent
from src.agents.solution_agent import SolutionAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.state.rca_state import RCAState


class RCAGraphBuilder:
    """Builds the deterministic RCA execution graph."""

    def __init__(
        self,
        log_fetcher_agent: LogFetcherAgent,
        driver_failure_agent: DriverFailureAgent,
        lineage_agent: LineageAgent,
        summarizer_agent: SummarizerAgent,
        category_agent: CategoryAgent,
        rca_agent: RCAAgent,
        solution_agent: SolutionAgent,
    ) -> None:
        """Initialize graph with injected node agents."""
        self._log_fetcher_agent = log_fetcher_agent
        self._driver_failure_agent = driver_failure_agent
        self._lineage_agent = lineage_agent
        self._summarizer_agent = summarizer_agent
        self._category_agent = category_agent
        self._rca_agent = rca_agent
        self._solution_agent = solution_agent

    def build(self) -> Any:
        """Build and compile LangGraph StateGraph."""
        graph = StateGraph(RCAState)
        graph.add_node("log_fetcher", self._log_fetcher_agent.run)
        graph.add_node("driver_failure", self._driver_failure_agent.run)
        graph.add_node("summarizer", self._summarizer_agent.run)
        graph.add_node("lineage", self._lineage_agent.run)
        graph.add_node("category", self._category_agent.run)
        graph.add_node("rca", self._rca_agent.run)
        graph.add_node("solution", self._solution_agent.run)

        graph.add_edge(START, "log_fetcher")
        graph.add_conditional_edges(
            "log_fetcher",
            self._route_after_log_fetcher,
            {"summarizer": "summarizer", "driver_failure": "driver_failure"},
        )
        graph.add_edge("summarizer", "lineage")
        graph.add_conditional_edges(
            "driver_failure",
            self._route_after_driver_failure,
            {"rca": "rca", "lineage": "lineage"},
        )
        graph.add_conditional_edges(
            "lineage",
            self._route_after_lineage,
            {"rca": "rca", "category": "category"},
        )
        graph.add_edge("category", "rca")
        graph.add_edge("rca", "solution")
        graph.add_edge("solution", END)
        return graph.compile()

    @classmethod
    def _route_after_log_fetcher(cls, state: RCAState) -> str:
        """Rule A: branch based on log existence."""
        return "summarizer" if bool(state["logs"]) else "driver_failure"

    @classmethod
    def _route_after_driver_failure(cls, state: RCAState) -> str:
        """Rule B: mandatory shortcut when logs missing and driver failure is true."""
        if not state["logs"] and state["driver_failure"]:
            return "rca"
        return "lineage"

    @classmethod
    def _route_after_lineage(cls, state: RCAState) -> str:
        """Rule C: branch based on category availability."""
        return "rca" if bool(state["category"]) else "category"


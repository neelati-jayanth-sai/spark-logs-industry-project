"""Agent Registry."""

from typing import Any
from src.agents.base_agent import BaseAgent

class AgentRegistry:
    """Registry to keep track of available agents."""

    def __init__(self) -> None:
        """Initialize the agent registry."""
        self._agents: dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        """Register an agent by its node name."""
        self._agents[name] = agent

    def get_agent(self, name: str) -> BaseAgent:
        """Retrieve an agent by name."""
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' is not registered in the AgentRegistry.")
        return self._agents[name]

    def get_all_agents(self) -> dict[str, BaseAgent]:
        """Get all registered agents."""
        return self._agents.copy()

    def clear(self) -> None:
        """Clear the registry."""
        self._agents.clear()

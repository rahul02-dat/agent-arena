from typing import Any, List
from arena.orchestration.base import BaseOrchestrator
from arena.core.protocols import Agent

class SequentialOrchestrator(BaseOrchestrator):
    def __init__(self, agents: List[Agent]) -> None:
        self.agents = agents
        self._current_index = 0

    def next_action(self) -> Any:
        if not self.agents:
            return None
        agent = self.agents[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.agents)
        return agent.act()

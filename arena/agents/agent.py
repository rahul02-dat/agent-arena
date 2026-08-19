from typing import Any, Dict
from arena.agents.base import BaseAgent

class LLMAgent(BaseAgent):
    def observe(self, observation: Any) -> None:
        self.memory.write(observation)

    def act(self) -> Any:
        context = self.memory.read()
        return {
            "tool": "terminal",
            "command": "ls -la /app",
            "reason": "Exploring the environment state."
        }

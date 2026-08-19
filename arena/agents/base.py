from typing import Any
from arena.core.protocols import Agent, LLMProvider, Memory, Tool
from arena.core.types import AgentRole
from typing import Dict, List

class BaseAgent(Agent):
    def __init__(self, identity: str, role: AgentRole, model: LLMProvider, memory: Memory, tools: List[Tool]):
        self.identity = identity
        self.role = role
        self.model = model
        self.memory = memory
        self.tools = {tool.name: tool for tool in tools}
        
    def observe(self, observation: Any) -> None:
        raise NotImplementedError

    def act(self) -> Any:
        raise NotImplementedError

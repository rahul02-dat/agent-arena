from typing import Dict, Type
from arena.tools.base import Tool

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Type[Tool]] = {}

    def register(self, tool_class: Type[Tool]) -> None:
        self._tools[tool_class.name] = tool_class

    def get(self, name: str) -> Type[Tool]:
        return self._tools[name]

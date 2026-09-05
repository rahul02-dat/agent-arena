from typing import Any, Dict, List, Type, Union
from arena.tools.base import Tool

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}

    def register(self, tool: Union[Tool, Type[Tool]]) -> None:
        name = getattr(tool, "name", None)
        if isinstance(name, property):
            # Property descriptor on a class without instance
            name = getattr(tool, "_name", None) or tool.__name__.lower()
        if not isinstance(name, str) or not name:
            raise ValueError(f"Tool {tool} must provide a non-empty string name.")
        self._tools[name] = tool

    def get(self, name: str) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

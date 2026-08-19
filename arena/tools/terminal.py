from typing import Any
from arena.tools.base import Tool

class TerminalTool(Tool):
    name: str = "terminal"
    description: str = "Execute terminal commands inside the task environment."

    def execute(self, command: str) -> Any:
        pass

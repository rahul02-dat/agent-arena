from typing import Any, Dict
from arena.tools.base import Tool
from arena.environments.base import BaseEnvironment

class TerminalTool(Tool):
    name: str = "terminal"
    description: str = "Executes shell commands inside the isolated task environment."
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute."
            }
        },
        "required": ["command"]
    }

    def __init__(self, environment: BaseEnvironment):
        self.environment = environment

    def execute(self, **kwargs: Any) -> Any:
        command = kwargs.get("command")
        if not command:
            return {"error": "No command provided."}
        timeout = kwargs.get("timeout")
        return self.environment.execute(command, timeout=timeout)

from typing import Any, Dict
from arena.tools.base import BaseTool
from arena.environments.base import BaseEnvironment

class TerminalTool(BaseTool):
    def __init__(self, environment: BaseEnvironment):
        self.environment = environment
        
    @property
    def name(self) -> str:
        return "terminal"
        
    @property
    def description(self) -> str:
        return "Executes shell commands inside the isolated task environment."
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute."
                }
            },
            "required": ["command"]
        }
        
    def execute(self, **kwargs) -> Any:
        command = kwargs.get("command")
        if not command:
            return {"error": "No command provided."}
        return self.environment.execute(command)

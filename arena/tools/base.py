from typing import Any, Dict
from arena.core.protocols import Tool as ToolProtocol

class Tool(ToolProtocol):
    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}

    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError

# Backwards compatibility alias
BaseTool = Tool

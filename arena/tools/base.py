from typing import Any
from arena.core.protocols import Tool as BaseTool

class Tool(BaseTool):
    name: str = ""
    description: str = ""

    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError

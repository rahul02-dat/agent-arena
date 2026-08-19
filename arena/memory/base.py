from typing import Any
from arena.core.protocols import Memory

class BaseMemory(Memory):
    def write(self, data: Any) -> None:
        raise NotImplementedError

    def read(self) -> Any:
        raise NotImplementedError

    def search(self, query: str) -> Any:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

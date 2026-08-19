from typing import Any, List
from arena.memory.base import BaseMemory

class LocalMemory(BaseMemory):
    def __init__(self) -> None:
        self._data: List[Any] = []

    def write(self, data: Any) -> None:
        self._data.append(data)

    def read(self) -> Any:
        return self._data

    def search(self, query: str) -> Any:
        return [item for item in self._data if query in str(item)]

    def clear(self) -> None:
        self._data.clear()

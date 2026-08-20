from typing import Any, Dict, List

from arena.memory.base import BaseMemory


class LocalMemory(BaseMemory):
    def __init__(self) -> None:
        self._messages: List[Dict[str, Any]] = []

    def write(self, data: Any) -> None:
        if isinstance(data, dict) and "role" in data:
            self._messages.append(dict(data))
            return

        self._messages.append(
            {
                "role": "user",
                "content": str(data),
            }
        )

    def read(self) -> List[Dict[str, Any]]:
        return [dict(message) for message in self._messages]

    def search(self, query: str) -> Any:
        query = query.lower()

        return [
            message
            for message in self._messages
            if query in str(message).lower()
        ]

    def clear(self) -> None:
        self._messages.clear()
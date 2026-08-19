from typing import Any
from arena.core.protocols import Environment

class BaseEnvironment(Environment):
    def create(self) -> None:
        raise NotImplementedError

    def reset(self) -> Any:
        raise NotImplementedError

    def observe(self) -> Any:
        raise NotImplementedError

    def execute(self, action: Any) -> Any:
        raise NotImplementedError

    def snapshot(self) -> None:
        raise NotImplementedError

    def destroy(self) -> None:
        raise NotImplementedError

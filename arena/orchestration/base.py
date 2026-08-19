from typing import Any
from arena.core.protocols import Orchestrator

class BaseOrchestrator(Orchestrator):
    def next_action(self) -> Any:
        raise NotImplementedError

from typing import Protocol, Any, Dict, List

class LLMProvider(Protocol):
    def chat(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        ...

    def generate(self, prompt: str) -> str:
        ...

class Agent(Protocol):
    def observe(self, observation: Any) -> None:
        ...

    def act(self) -> Any:
        ...

class Environment(Protocol):
    def create(self) -> None:
        ...

    def reset(self) -> Any:
        ...

    def observe(self) -> Any:
        ...

    def execute(self, action: Any) -> Any:
        ...

    def snapshot(self) -> None:
        ...

    def destroy(self) -> None:
        ...

class Tool(Protocol):
    name: str
    description: str

    def execute(self, **kwargs: Any) -> Any:
        ...

class Memory(Protocol):
    def write(self, data: Any) -> None:
        ...

    def read(self) -> Any:
        ...

    def search(self, query: str) -> Any:
        ...

    def clear(self) -> None:
        ...

class Evaluator(Protocol):
    def evaluate(self, task: Any, state: Any, protected_data: Any) -> Any:
        ...

class Orchestrator(Protocol):
    def next_action(self) -> Any:
        ...

class TrajectoryRecorder(Protocol):
    def record(self, event: Any) -> None:
        ...

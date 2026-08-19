from typing import Any
from arena.core.protocols import Evaluator as BaseEvaluator

class Evaluator(BaseEvaluator):
    def evaluate(self, task: Any, state: Any, protected_data: Any) -> Any:
        pass

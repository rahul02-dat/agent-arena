from typing import Any, Dict
from arena.environments.base import BaseEnvironment

class Evaluator:
    def __init__(self, environment: BaseEnvironment):
        self.environment = environment
        
    def evaluate(self) -> Dict[str, Any]:
        res = self.environment.execute("bash tests/test.sh")
        success = res.get("exit_code", -1) == 0
        return {
            "success": success,
            "score": 1.0 if success else 0.0,
            "details": res.get("output", "")
        }

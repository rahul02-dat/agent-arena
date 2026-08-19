from typing import Any, Dict
from arena.environments.base import BaseEnvironment

class Evaluator:
    def __init__(self, environment: BaseEnvironment):
        self.environment = environment
        
    def evaluate(self) -> Dict[str, Any]:
        if hasattr(self.environment, "task_dir") and hasattr(self.environment, "copy_to_container"):
            tests_path = self.environment.task_dir / "evaluator" / "tests"
            if tests_path.exists():
                self.environment.copy_to_container(str(tests_path), "/")
                res = self.environment.execute("bash /tests/test.sh")
            else:
                res = {"exit_code": -1, "output": f"Tests not found at {tests_path}"}
        else:
            res = self.environment.execute("bash tests/test.sh")

        # The test.sh returns 0 regardless of test success, we need to read /logs/verifier/reward.txt
        reward_res = self.environment.execute("cat /logs/verifier/reward.txt")
        score = 0.0
        if reward_res.get("exit_code") == 0:
            try:
                score = float(reward_res.get("output", "0").strip())
            except ValueError:
                pass
        
        success = score > 0.0
        
        return {
            "success": success,
            "score": score,
            "details": res.get("output", "")
        }

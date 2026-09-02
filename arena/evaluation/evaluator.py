import json
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

        ctrf_res = self.environment.execute("cat /logs/verifier/ctrf.json")
        success = False
        score = 0.0
        metrics = {}
        failure_reason = None
        
        if ctrf_res.get("exit_code") == 0:
            try:
                ctrf_data = json.loads(ctrf_res.get("stdout", "{}"))
                summary = ctrf_data.get("results", {}).get("summary", {})
                passed = summary.get("passed", 0)
                failed = summary.get("failed", 0)
                total = passed + failed
                
                if total > 0:
                    score = float(passed) / total
                    success = (failed == 0)
                
                metrics = summary
                
                if failed > 0:
                    failure_reason = "Some evaluation tests failed."
                
            except json.JSONDecodeError:
                failure_reason = "Failed to parse CTRF evaluation output."
        else:
            failure_reason = "Evaluation CTRF report not found or could not be read."

        return {
            "success": success,
            "score": score,
            "metrics": metrics,
            "failure_reason": failure_reason,
            "details": res.get("output", "")
        }

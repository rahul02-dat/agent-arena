import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from arena.environments.base import BaseEnvironment
from arena.core.protocols import Evaluator as EvaluatorProtocol


class BaseEvaluator(EvaluatorProtocol):
    def __init__(self, environment: BaseEnvironment, task_dir: Optional[Path | str] = None):
        self.environment = environment
        self.task_dir = Path(task_dir) if task_dir else getattr(environment, "task_dir", None)

    def validate_submission(self) -> Tuple[bool, Optional[str]]:
        """Environment-side submission validation. Can be overridden by task evaluators."""
        return True, None

    def evaluate(
        self,
        task: Any = None,
        state: Any = None,
        protected_data: Any = None,
    ) -> Dict[str, Any]:
        """Generic evaluation method. Subclasses should override with task-specific logic."""
        return {
            "success": False,
            "score": 0.0,
            "metrics": {},
            "failure_reason": "Default BaseEvaluator has no task-specific evaluation defined.",
        }


def get_evaluator(
    environment: BaseEnvironment,
    task_dir: Optional[Path | str] = None,
) -> BaseEvaluator:
    """Factory to load task-specific evaluator if available, otherwise return BaseEvaluator."""
    t_dir = Path(task_dir) if task_dir else getattr(environment, "task_dir", None)
    if t_dir:
        t_dir = Path(t_dir)
        evaluator_py = t_dir / "evaluator" / "evaluator.py"
        if evaluator_py.exists():
            mod_name = f"tasks.{t_dir.name}.evaluator.evaluator"
            try:
                import sys
                if mod_name in sys.modules:
                    mod = sys.modules[mod_name]
                else:
                    spec = importlib.util.spec_from_file_location(mod_name, str(evaluator_py))
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[mod_name] = mod
                        spec.loader.exec_module(mod)
                    else:
                        mod = None

                if mod:
                    eval_cls = getattr(mod, "TaskEvaluator", None)
                    if not eval_cls:
                        for attr_name in dir(mod):
                            attr = getattr(mod, attr_name)
                            if (
                                isinstance(attr, type)
                                and issubclass(attr, BaseEvaluator)
                                and attr is not BaseEvaluator
                            ):
                                eval_cls = attr
                                break
                    if eval_cls:
                        return eval_cls(environment=environment, task_dir=t_dir)
            except Exception:
                pass


    return BaseEvaluator(environment=environment, task_dir=t_dir)


# Backwards compatibility alias
Evaluator = BaseEvaluator

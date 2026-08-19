import json
from pathlib import Path
from typing import Any, Dict, List

class TrajectoryRecorder:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = []
        
    def record_step(self, step_data: Dict[str, Any]) -> None:
        self.history.append(step_data)
        
    def save(self, task_name: str) -> None:
        file_path = self.output_dir / f"{task_name}_trajectory.json"
        with open(file_path, "w") as f:
            json.dump(self.history, f, indent=2)

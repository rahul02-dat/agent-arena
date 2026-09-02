import json
import time
from pathlib import Path
from typing import Any, Dict

class TrajectoryRecorder:
    def __init__(self, output_dir: str = "results", experiment_id: str = None):
        self.output_dir = Path(output_dir)
        self.experiment_id = experiment_id or f"exp_{int(time.time())}"
        self.episode_id = f"episode_{int(time.time())}"
        self.episode_dir = self.output_dir / self.experiment_id / "episodes"
        self.episode_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.episode_dir / f"{self.episode_id}.jsonl"
        
    def record_step(self, step_data: Dict[str, Any]) -> None:
        if "schema_version" not in step_data:
            step_data["schema_version"] = "1.0"
        if "episode_id" not in step_data:
            step_data["episode_id"] = self.episode_id
            
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(step_data) + "\n")
        
    def save(self, task_name: str) -> None:
        # Saving is handled incrementally, nothing to do here.
        pass

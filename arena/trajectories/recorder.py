import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from arena.trajectories.schema import ExperimentManifest, TrajectoryEvent


class TrajectoryRecorder:
    def __init__(
        self,
        output_dir: str = "results",
        experiment_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        manifest: Optional[Union[ExperimentManifest, Dict[str, Any]]] = None,
    ):
        self.output_dir = Path(output_dir)
        ts = int(time.time())
        rand_suffix = uuid.uuid4().hex[:6]
        self.experiment_id = experiment_id or f"exp_{ts}_{rand_suffix}"
        self.episode_id = episode_id or f"episode_{ts}_{rand_suffix}"

        self.experiment_dir = self.output_dir / self.experiment_id
        self.episode_dir = self.experiment_dir / "episodes"
        self.episode_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.episode_dir / f"{self.episode_id}.jsonl"

        self.step_count = 0
        self.tool_call_count = 0
        self.start_time = time.time()

        if manifest:
            self.write_manifest(manifest)

    def write_manifest(self, manifest: Union[ExperimentManifest, Dict[str, Any]]) -> None:
        if isinstance(manifest, dict):
            manifest_dict = dict(manifest)
            manifest_dict["experiment_id"] = self.experiment_id
            manifest_obj = ExperimentManifest(**manifest_dict)
        else:
            manifest_obj = manifest

        manifest_path = self.experiment_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest_obj.model_dump_json(indent=2, by_alias=True))


    def record_step(
        self,
        step_data: Union[TrajectoryEvent, Dict[str, Any]],
        step: Optional[int] = None,
        agent_id: Optional[str] = None,
        agent_role: Optional[str] = None,
    ) -> TrajectoryEvent:
        if isinstance(step_data, TrajectoryEvent):
            event = step_data
        else:
            event_dict = dict(step_data)
            event_type = event_dict.pop("type", event_dict.pop("event_type", "generic"))
            event_step = step if step is not None else event_dict.pop("step", self.step_count)
            schema_ver = event_dict.pop("schema_version", "1.0")
            ep_id = event_dict.pop("episode_id", self.episode_id)
            ev_agent_id = agent_id or event_dict.pop("agent_id", None)
            ev_agent_role = agent_role or event_dict.pop("agent_role", None)

            data = event_dict.get("data", event_dict)

            event = TrajectoryEvent(
                schema_version=schema_ver,
                episode_id=ep_id,
                step=event_step,
                event_type=event_type,
                agent_id=ev_agent_id,
                agent_role=ev_agent_role,
                data=data,
            )

        if event.event_type in ("tool_result", "tool_call"):
            self.tool_call_count += 1

        self.step_count = max(self.step_count, event.step)

        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

        return event

    def save(self, task_name: str) -> None:
        # Saving is done incrementally per event
        pass

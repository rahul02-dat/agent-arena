from typing import Any, List
from arena.core.protocols import TrajectoryRecorder as BaseRecorder
from arena.trajectories.schema import Episode, TrajectoryStep

class TrajectoryRecorder(BaseRecorder):
    def __init__(self, episode_id: str, task_id: str) -> None:
        self.episode = Episode(episode_id=episode_id, task_id=task_id, steps=[])

    def record(self, event: Any) -> None:
        if isinstance(event, TrajectoryStep):
            self.episode.steps.append(event)

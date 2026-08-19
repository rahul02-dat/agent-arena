from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

class Observation(BaseModel):
    state: Any
    timestamp: datetime

class Action(BaseModel):
    action_type: str
    payload: Any

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    tool_name: str
    result: Any
    success: bool

class RewardEvent(BaseModel):
    value: float
    reason: str

class EvaluationResult(BaseModel):
    success: bool
    score: float
    metrics: Dict[str, Any]
    failure_reason: Optional[str] = None

class TrajectoryStep(BaseModel):
    step_id: int
    observation: Observation
    action: Action
    reward: Optional[RewardEvent] = None

class Episode(BaseModel):
    episode_id: str
    task_id: str
    steps: List[TrajectoryStep]
    evaluation: Optional[EvaluationResult] = None

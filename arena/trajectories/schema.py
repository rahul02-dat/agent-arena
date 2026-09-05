from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExperimentManifest(BaseModel):
    model_config = {"populate_by_name": True}

    schema_version: str = "1.0"
    experiment_id: str
    task_id: str
    task_version: str = "1.0"
    model_name: str
    model_params: Dict[str, Any] = Field(default_factory=dict, alias="model_config")

    agent_config: Dict[str, Any] = Field(default_factory=dict)
    orchestration_config: Dict[str, Any] = Field(default_factory=dict)
    limits: Dict[str, Any] = Field(default_factory=dict)
    environment_config: Dict[str, Any] = Field(default_factory=dict)
    software_version: str = "0.1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TrajectoryEvent(BaseModel):
    schema_version: str = "1.0"
    episode_id: str
    step: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str
    agent_id: Optional[str] = None
    agent_role: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class Observation(BaseModel):
    state: Any
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Action(BaseModel):
    action_type: str
    payload: Any


class ToolCall(BaseModel):
    tool_call_id: str
    tool_name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    tool_name: str
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    error_type: Optional[str] = None


class RewardEvent(BaseModel):
    value: float
    reason: str


class EvaluationResult(BaseModel):
    success: bool
    score: float
    metrics: Dict[str, Any] = Field(default_factory=dict)
    failure_reason: Optional[str] = None


class TrajectoryStep(BaseModel):
    step_id: int
    observation: Observation
    action: Action
    reward: Optional[RewardEvent] = None


class Episode(BaseModel):
    episode_id: str
    task_id: str
    steps: List[TrajectoryStep] = Field(default_factory=list)
    evaluation: Optional[EvaluationResult] = None

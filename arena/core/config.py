from pydantic import BaseModel
from typing import List, Optional

class ModelConfig(BaseModel):
    name: str
    temperature: float = 0.0

class AgentConfig(BaseModel):
    role: str
    model: ModelConfig

class EnvironmentConfig(BaseModel):
    runtime: str
    network: bool = False

class EvaluationConfig(BaseModel):
    correctness: bool = True

class ExperimentConfig(BaseModel):
    task: str
    agents: List[AgentConfig]
    environment: EnvironmentConfig
    evaluation: EvaluationConfig

class ArenaConfig(BaseModel):
    experiment: ExperimentConfig

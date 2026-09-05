from enum import Enum
from typing import NewType

AgentId = NewType('AgentId', str)
TaskId = NewType('TaskId', str)
EpisodeId = NewType('EpisodeId', str)

class ActionType(Enum):
    TOOL_CALL = "TOOL_CALL"
    MESSAGE = "MESSAGE"
    STOP = "STOP"
    SUBMIT = "SUBMIT"


class AgentRole(Enum):
    EXPLORER = "EXPLORER"
    RESEARCHER = "RESEARCHER"
    EXECUTOR = "EXECUTOR"
    CRITIC = "CRITIC"
    VERIFIER = "VERIFIER"
    ORCHESTRATOR = "ORCHESTRATOR"

class EpisodeStatus(Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"

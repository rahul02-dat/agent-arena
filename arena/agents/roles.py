from arena.core.types import AgentRole
from dataclasses import dataclass

@dataclass
class RoleDefinition:
    role: AgentRole
    description: str
    constraints: str

ROLES = {
    AgentRole.EXPLORER: RoleDefinition(
        role=AgentRole.EXPLORER,
        description="Explore the environment and gather information.",
        constraints="Cannot make irreversible changes."
    ),
    AgentRole.RESEARCHER: RoleDefinition(
        role=AgentRole.RESEARCHER,
        description="Analyze information and formulate hypotheses.",
        constraints="Must base conclusions on observed facts."
    ),
    AgentRole.EXECUTOR: RoleDefinition(
        role=AgentRole.EXECUTOR,
        description="Execute commands and scripts.",
        constraints="Must execute safely."
    ),
    AgentRole.CRITIC: RoleDefinition(
        role=AgentRole.CRITIC,
        description="Critique plans and results.",
        constraints="Must provide constructive feedback."
    ),
    AgentRole.VERIFIER: RoleDefinition(
        role=AgentRole.VERIFIER,
        description="Verify solutions.",
        constraints="Must be thorough."
    ),
    AgentRole.ORCHESTRATOR: RoleDefinition(
        role=AgentRole.ORCHESTRATOR,
        description="Coordinate other agents.",
        constraints="Must distribute work effectively."
    )
}

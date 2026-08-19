from arena.core.types import AgentRole
from arena.agents.roles import ROLES

def test_agent_roles_exist():
    assert AgentRole.EXPLORER in ROLES

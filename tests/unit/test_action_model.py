from arena.core.types import ActionType, AgentRole
from arena.agents.agent import LLMAgent
from arena.memory.local import LocalMemory
from arena.tools.terminal import TerminalTool


class MockLLMProvider:
    def __init__(self, response: dict):
        self.response = response

    def chat(self, messages, tools=None):
        return self.response

    def generate(self, prompt: str):
        return ""


class DummyEnvironment:
    def execute(self, cmd: str, timeout: int | None = None):
        return {"exit_code": 0, "stdout": "", "stderr": ""}


def test_action_type_enum():
    assert ActionType.SUBMIT.value == "SUBMIT"
    assert ActionType.TOOL_CALL.value == "TOOL_CALL"


def test_agent_parses_submit_tool_call():
    mock_response = {
        "message": {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "submit",
                        "arguments": '{"reason": "Recovered private key successfully"}',
                    },
                }
            ],
        }
    }
    llm = MockLLMProvider(mock_response)
    env = DummyEnvironment()
    agent = LLMAgent(
        identity="Agent-Test",
        role=AgentRole.EXECUTOR,
        model=llm,
        memory=LocalMemory(),
        tools=[TerminalTool(environment=env)],
        objective="Recover key",
        instructions="Test",
    )

    action = agent.act()
    assert action["type"] == ActionType.SUBMIT.value
    assert action["tool"] == "submit"
    assert action["arguments"]["reason"] == "Recovered private key successfully"


def test_schema_driven_action_validation_missing_required():
    env = DummyEnvironment()
    agent = LLMAgent(
        identity="Agent-Test",
        role=AgentRole.EXECUTOR,
        model=MockLLMProvider({}),
        memory=LocalMemory(),
        tools=[TerminalTool(environment=env)],
        objective="Recover key",
        instructions="Test",
    )

    # Missing required 'command' argument for terminal tool
    invalid_action = {
        "type": ActionType.TOOL_CALL.value,
        "tool": "terminal",
        "arguments": {},
    }
    err = agent._validate_action(invalid_action)
    assert err is not None
    assert "missing required argument: 'command'" in err


def test_schema_driven_action_validation_empty_string():
    env = DummyEnvironment()
    agent = LLMAgent(
        identity="Agent-Test",
        role=AgentRole.EXECUTOR,
        model=MockLLMProvider({}),
        memory=LocalMemory(),
        tools=[TerminalTool(environment=env)],
        objective="Recover key",
        instructions="Test",
    )

    # Empty string for required 'command' argument
    invalid_action = {
        "type": ActionType.TOOL_CALL.value,
        "tool": "terminal",
        "arguments": {"command": "   "},
    }
    err = agent._validate_action(invalid_action)
    assert err is not None
    assert "requires a non-empty string" in err


def test_schema_driven_action_validation_valid():
    env = DummyEnvironment()
    agent = LLMAgent(
        identity="Agent-Test",
        role=AgentRole.EXECUTOR,
        model=MockLLMProvider({}),
        memory=LocalMemory(),
        tools=[TerminalTool(environment=env)],
        objective="Recover key",
        instructions="Test",
    )

    valid_action = {
        "type": ActionType.TOOL_CALL.value,
        "tool": "terminal",
        "arguments": {"command": "ls -la"},
    }
    err = agent._validate_action(valid_action)
    assert err is None

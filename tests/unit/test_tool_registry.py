import pytest
from arena.tools.base import Tool
from arena.tools.terminal import TerminalTool
from arena.tools.registry import ToolRegistry


class DummyEnvironment:
    def execute(self, cmd: str, timeout: int | None = None):
        return {"exit_code": 0, "stdout": f"executed {cmd}", "stderr": ""}


class CustomTool(Tool):
    name = "custom_tool"
    description = "A custom testing tool."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    }

    def execute(self, **kwargs):
        return {"result": kwargs.get("query")}


def test_tool_class_attributes():
    assert TerminalTool.name == "terminal"
    assert "command" in TerminalTool.input_schema["required"]
    assert CustomTool.name == "custom_tool"


def test_tool_registry_with_class_and_instance():
    registry = ToolRegistry()

    # Register class
    registry.register(CustomTool)
    assert registry.get("custom_tool") is CustomTool

    # Register instance
    dummy_env = DummyEnvironment()
    term_instance = TerminalTool(environment=dummy_env)
    registry.register(term_instance)
    assert registry.get("terminal") is term_instance

    # List tools
    tool_list = registry.list_tools()
    assert "custom_tool" in tool_list
    assert "terminal" in tool_list


def test_tool_registry_unregistered_key_error():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.get("non_existent_tool")


def test_tool_registry_invalid_tool():
    registry = ToolRegistry()
    with pytest.raises(ValueError):
        registry.register(object())

import json
from typing import Any, Dict, List, Optional

from arena.agents.base import BaseAgent
from arena.core.protocols import LLMProvider, Memory, Tool
from arena.core.types import AgentRole


class LLMAgent(BaseAgent):
    def __init__(
        self,
        identity: str,
        role: AgentRole,
        model: LLMProvider,
        memory: Memory,
        tools: List[Tool],
        objective: str,
        instructions: str,
        max_invalid_actions: int = 5,
    ):
        super().__init__(
            identity=identity,
            role=role,
            model=model,
            memory=memory,
            tools=tools,
        )
        self.objective = objective
        self.task_instructions = instructions
        self.max_invalid_actions = max_invalid_actions
        self.invalid_action_count = 0
        self._last_action = None

    def observe(self, observation: Any) -> None:
        if isinstance(observation, dict) and "role" in observation:
            self.memory.write(observation)
            return

        self.memory.write(
            {
                "role": "user",
                "content": str(observation),
            }
        )

    def act(self) -> Dict[str, Any]:
        messages = self._build_messages()
        tools = self._formatted_tools()

        response = self.model.chat(
            messages=messages,
            tools=tools,
        )

        if "error" in response:
            return {
                "type": "error",
                "error": response["error"],
            }

        message = response.get("message", {})

        action = self._parse_structured_tool_call(message)

        if action is None:
            action = self._parse_textual_tool_call(
                message.get("content", "")
            )

        if action is None:
            self.invalid_action_count += 1

            return {
                "type": "invalid_action",
                "reason": "The model did not produce a valid tool call.",
                "content": message.get("content", ""),
                "invalid_action_count": self.invalid_action_count,
            }

        validation_error = self._validate_action(action)

        if validation_error:
            self.invalid_action_count += 1

            return {
                "type": "invalid_action",
                "reason": validation_error,
                "action": action,
                "invalid_action_count": self.invalid_action_count,
            }

        if self._is_exact_duplicate(action):
            return {
                "type": "duplicate_action",
                "reason": "This exact action is identical to the previous action.",
                "action": action,
            }

        self.invalid_action_count = 0
        self._last_action = dict(action)

        return action

    def _build_messages(self) -> list[Dict[str, Any]]:
        system_prompt = f"""You are {self.identity}.

Your role is: {self.role.name}.

TASK OBJECTIVE:
{self.objective}

TASK INSTRUCTIONS:
{self.task_instructions}

You are operating inside an isolated task environment.

Rules:
1. Work toward the stated objective.
2. Use the available tools to inspect and modify only the task environment.
3. Do not repeat an identical action unless new information justifies it.
4. Inspect relevant task files before making unsupported assumptions.
5. Tool results are authoritative observations of the environment.
6. Do not claim success. Use the submit tool only when you believe the required task artifact has been produced.
7. If a previous response was rejected as invalid, correct the format and try again.
"""

        return [
            {
                "role": "system",
                "content": system_prompt,
            },
            *self.memory.read(),
        ]

    def _formatted_tools(self) -> list[Dict[str, Any]]:
        tools = []

        for tool in self.tools.values():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
            )

        tools.append(
            {
                "type": "function",
                "function": {
                    "name": "submit",
                    "description": (
                        "Submit the task for evaluation. "
                        "Only use this after producing the required artifact."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": (
                                    "Brief explanation of why the task "
                                    "is ready for evaluation."
                                ),
                            }
                        },
                        "required": ["reason"],
                    },
                },
            }
        )

        return tools

    def _parse_structured_tool_call(
        self,
        message: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            return None

        tool_call = tool_calls[0]
        function = tool_call.get("function", {})

        name = function.get("name")
        arguments = function.get("arguments", {})

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return None

        if not isinstance(arguments, dict):
            return None

        return {
            "type": "tool_call",
            "tool": name,
            "arguments": arguments,
        }

    def _parse_textual_tool_call(
        self,
        content: str,
    ) -> Optional[Dict[str, Any]]:
        if not content or not content.strip():
            return None

        payload = self._extract_json_object(content)

        if not payload:
            return None

        name = (
            payload.get("tool")
            or payload.get("name")
        )

        arguments = (
            payload.get("arguments")
            or payload.get("parameters")
        )

        if arguments is None:
            if "command" in payload:
                arguments = {
                    "command": payload["command"],
                }
            else:
                arguments = {}

        if not isinstance(name, str):
            return None

        if not isinstance(arguments, dict):
            return None

        return {
            "type": "tool_call",
            "tool": name,
            "arguments": arguments,
        }

    @staticmethod
    def _extract_json_object(
        content: str,
    ) -> Optional[Dict[str, Any]]:
        decoder = json.JSONDecoder()

        for index, char in enumerate(content):
            if char != "{":
                continue

            try:
                value, _ = decoder.raw_decode(content[index:])

                if isinstance(value, dict):
                    return value

            except json.JSONDecodeError:
                continue

        return None

    def _validate_action(
        self,
        action: Dict[str, Any],
    ) -> Optional[str]:
        tool_name = action.get("tool")

        if tool_name == "submit":
            reason = action.get("arguments", {}).get("reason")

            if not isinstance(reason, str) or not reason.strip():
                return "Submit requires a non-empty reason."

            return None

        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name!r}"

        arguments = action.get("arguments")

        if not isinstance(arguments, dict):
            return "Tool arguments must be a JSON object."

        if tool_name == "terminal":
            command = arguments.get("command")

            if not isinstance(command, str) or not command.strip():
                return "Terminal requires a non-empty 'command'."

        return None

    def _is_exact_duplicate(
        self,
        action: Dict[str, Any],
    ) -> bool:
        if self._last_action is None:
            return False

        return (
            action.get("tool") == self._last_action.get("tool")
            and action.get("arguments") == self._last_action.get("arguments")
        )
import json
import tempfile
from pathlib import Path

from arena.agents.agent import LLMAgent
from arena.core.types import ActionType, AgentRole
from arena.environments.docker import DockerEnvironment
from arena.evaluation.evaluator import get_evaluator
from arena.memory.local import LocalMemory
from arena.orchestration.sequential import SequentialOrchestrator
from arena.tools.terminal import TerminalTool
from arena.trajectories.recorder import TrajectoryRecorder
from tasks.ecdsa_nonce_bias_001.evaluator.evaluator import G, scalar_mult


class ScriptedMockModel:
    """Deterministic mock agent that walks through a scripted sequence of actions."""
    def __init__(self, actions: list[dict]):
        self.actions = actions
        self.call_idx = 0

    def chat(self, messages, tools=None):
        if self.call_idx < len(self.actions):
            action = self.actions[self.call_idx]
            self.call_idx += 1
            return {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": f"call_{self.call_idx}",
                            "type": "function",
                            "function": {
                                "name": action["tool"],
                                "arguments": json.dumps(action["arguments"]),
                            },
                        }
                    ],
                }
            }
        return {"error": "No more scripted actions"}

    def generate(self, prompt: str) -> str:
        return ""


def test_complete_episode_with_deterministic_mock_agent():
    task_dir = Path("tasks") / "ecdsa_nonce_bias_001"

    # Known test keypair
    test_d = 0x4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123
    pub_point = scalar_mult(test_d, G)
    ground_truth = {
        "private_key_hex": hex(test_d),
        "public_key": {
            "x": hex(pub_point[0]),
            "y": hex(pub_point[1]),
        },
    }

    with tempfile.TemporaryDirectory() as results_dir:
        env = DockerEnvironment(
            task_dir=str(task_dir),
            cpus=1,
            memory_mb=512,
            network="disabled",
        )
        env.create()

        recorder = TrajectoryRecorder(
            output_dir=results_dir,
            manifest={
                "task_id": "ecdsa_nonce_bias_001",
                "task_version": "1.0",
                "model_name": "mock_scripted",
            },
        )

        evaluator = get_evaluator(environment=env, task_dir=task_dir)

        # Scripted actions:
        # 1. Premature submit without private_key.txt (MUST BE REJECTED)
        # 2. Write private key to /app/private_key.txt
        # 3. Valid submit
        scripted_actions = [
            {"tool": "submit", "arguments": {"reason": "Premature submit attempt"}},
            {
                "tool": "terminal",
                "arguments": {
                    "command": f"echo '{hex(test_d)}' > /app/private_key.txt",
                },
            },
            {"tool": "submit", "arguments": {"reason": "Recovered valid private key"}},
        ]

        model = ScriptedMockModel(scripted_actions)
        terminal_tool = TerminalTool(environment=env)
        agent = LLMAgent(
            identity="MockAgent-1",
            role=AgentRole.EXECUTOR,
            model=model,
            memory=LocalMemory(),
            tools=[terminal_tool],
            objective="Recover ECDSA private key",
            instructions="Write to /app/private_key.txt",
        )
        orchestrator = SequentialOrchestrator(agents=[agent])

        # Step 0: Observation
        obs = env.observe()
        agent.observe({"role": "user", "content": obs})
        recorder.record_step({"type": "observation", "content": obs}, step=0)

        # Run loop
        submitted = False
        rejection_witnessed = False

        for step in range(1, 10):
            action = orchestrator.next_action()
            recorder.record_step({"type": "action", "content": action}, step=step)

            if action.get("type") == ActionType.SUBMIT.value:
                # Pre-submission check via evaluator
                is_valid, reject_reason = evaluator.validate_submission()
                if not is_valid:
                    rejection_witnessed = True
                    agent.observe(
                        {"role": "user", "content": f"Submission rejected: {reject_reason}. Continue working."}
                    )
                    continue

                submitted = True
                recorder.record_step(
                    {"type": "submission", "content": action.get("arguments")},
                    step=step,
                )
                break

            # Execute tool
            tool_name = action.get("tool")
            args = action.get("arguments", {})
            tool = agent.tools[tool_name]
            result = tool.execute(**args)

            recorder.record_step(
                {"type": "tool_result", "tool": tool_name, "content": result},
                step=step,
            )
            tool_call_id = f"call_{step}"
            agent.observe(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {"name": tool_name, "arguments": args},
                        }
                    ],
                }
            )
            agent.observe(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": json.dumps(result),
                }
            )

        # 1. Verify mandatory regression check: rejection was witnessed
        assert rejection_witnessed is True, "Premature submit must be rejected!"

        # 2. Verify submission succeeded after writing the key
        assert submitted is True, "Agent must successfully submit valid artifact."

        # 3. Evaluate using protected data
        evaluation = evaluator.evaluate(protected_data=ground_truth)
        assert evaluation["success"] is True
        assert evaluation["score"] == 1.0
        assert evaluation["metrics"]["format_valid"] is True
        assert evaluation["metrics"]["matches_ground_truth"] is True
        assert evaluation["metrics"]["rederives_public_key"] is True

        recorder.record_step({"type": "evaluation", "content": evaluation}, step=recorder.step_count + 1)

        # 4. Clean up container
        env.destroy()
        assert env.container is None

        # 5. Verify trajectory recorded
        assert recorder.file_path.exists()
        with open(recorder.file_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) >= 5
        event_types = [l["event_type"] for l in lines]
        assert "observation" in event_types
        assert "action" in event_types
        assert "tool_result" in event_types
        assert "submission" in event_types
        assert "evaluation" in event_types

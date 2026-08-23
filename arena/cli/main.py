import tomllib
from pathlib import Path
from typing import Any, Dict

import typer

from arena.agents.agent import LLMAgent
from arena.core.types import AgentRole
from arena.environments.docker import DockerEnvironment
from arena.evaluation.evaluator import Evaluator
from arena.memory.local import LocalMemory
from arena.models.ollama import OllamaProvider
from arena.tools.terminal import TerminalTool
from arena.trajectories.recorder import TrajectoryRecorder


app = typer.Typer(
    help="Agent Arena CLI",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    pass


def build_agent_task_context(
    config: Dict[str, Any],
) -> tuple[str, str]:
    agent_task = config.get("agent_task", {})

    objective = agent_task.get(
        "objective",
        "Complete the task and produce the required artifact.",
    ).strip()

    instructions = agent_task.get(
        "instructions",
        "",
    ).strip()

    return objective, instructions


@app.command()
def run(
    task: str,
    max_steps: int = typer.Option(
        100,
        min=1,
        help="Maximum number of agent steps.",
    ),
    max_invalid_actions: int = typer.Option(
        3,
        min=1,
        help="Maximum consecutive invalid model actions.",
    ),
) -> None:
    typer.echo(f"Starting task: {task}")

    task_path = Path("tasks") / task / "task.yaml"

    if not task_path.exists():
        typer.echo(
            f"Error: configuration not found at {task_path}"
        )
        raise typer.Exit(code=1)

    with task_path.open("rb") as file:
        config = tomllib.load(file)

    task_name = config.get(
        "task",
        {},
    ).get(
        "name",
        task,
    )

    objective, task_instructions = build_agent_task_context(config)

    typer.echo(f"Loaded task: {task_name}")
    typer.echo(f"Objective: {objective}")

    env = DockerEnvironment(
        task_dir=str(task_path.parent),
    )

    recorder = TrajectoryRecorder()
    submitted = False
    evaluation_ran = False

    try:
        env.create()

        model = OllamaProvider(
            model_name="llama3.2",
        )

        memory = LocalMemory()

        terminal_tool = TerminalTool(
            environment=env,
        )

        agent = LLMAgent(
            identity="Agent-1",
            role=AgentRole.EXECUTOR,
            model=model,
            memory=memory,
            tools=[terminal_tool],
            objective=objective,
            instructions=task_instructions,
            max_invalid_actions=max_invalid_actions,
        )

        evaluator = Evaluator(
            environment=env,
        )

        typer.echo(
            "\n--- Starting Orchestrator Loop ---"
        )

        initial_observation = env.observe()

        agent.observe(
            {
                "role": "user",
                "content": (
                    "Initial environment observation:\n"
                    f"{initial_observation}"
                ),
            }
        )

        recorder.record_step(
            {
                "type": "observation",
                "content": initial_observation,
            }
        )

        invalid_actions = 0

        for step in range(1, max_steps + 1):
            typer.echo(f"\nStep {step}:")

            action = agent.act()

            typer.echo(
                f"Agent Action: {action}"
            )

            recorder.record_step(
                {
                    "type": "action",
                    "content": action,
                }
            )

            action_type = action.get("type")

            if action_type == "error":
                invalid_actions += 1

                feedback = (
                    "Model/runtime error:\n"
                    f"{action.get('error')}\n"
                    "Try again using an available tool."
                )

                agent.observe(
                    {
                        "role": "user",
                        "content": feedback,
                    }
                )

                if invalid_actions >= max_invalid_actions:
                    typer.echo(
                        "Too many invalid actions."
                    )
                    break

                continue

            if action_type == "invalid_action":
                invalid_actions += 1

                feedback = (
                    "Your previous response was not a valid tool call.\n"
                    f"Reason: {action.get('reason')}\n"
                    "Use one of the available tools and provide valid JSON arguments."
                )

                agent.observe(
                    {
                        "role": "user",
                        "content": feedback,
                    }
                )

                recorder.record_step(
                    {
                        "type": "invalid_action",
                        "content": action,
                    }
                )

                if invalid_actions >= max_invalid_actions:
                    typer.echo(
                        "Too many invalid actions."
                    )
                    break

                continue

            if action_type == "duplicate_action":
                feedback = (
                    "Your previous proposed action is an exact duplicate "
                    "of the immediately preceding action. Do not repeat it "
                    "without new information. Choose a different action."
                )

                agent.observe(
                    {
                        "role": "user",
                        "content": feedback,
                    }
                )

                recorder.record_step(
                    {
                        "type": "duplicate_action",
                        "content": action,
                    }
                )

                continue

            invalid_actions = 0

            tool_name = action.get("tool")
            arguments = action.get(
                "arguments",
                {},
            )

            if tool_name == "submit":
                submitted = True

                reason = arguments.get(
                    "reason",
                    "",
                )

                typer.echo(
                    f"Agent submitted task: {reason}"
                )

                recorder.record_step(
                    {
                        "type": "submission",
                        "content": {
                            "reason": reason,
                        },
                    }
                )

                break

            tool = agent.tools.get(tool_name)

            if tool is None:
                agent.observe(
                    {
                        "role": "user",
                        "content": (
                            f"Tool {tool_name!r} is unavailable. "
                            "Choose an available tool."
                        ),
                    }
                )
                continue

            result = tool.execute(**arguments)

            recorder.record_step(
                {
                    "type": "tool_result",
                    "tool": tool_name,
                    "arguments": arguments,
                    "content": result,
                }
            )

            agent.observe(
                {
                    "role": "assistant",
                    "content": (
                        f"Called tool {tool_name} "
                        f"with arguments {arguments}."
                    ),
                }
            )

            agent.observe(
                {
                    "role": "user",
                    "content": (
                        f"Tool result from {tool_name}:\n"
                        f"{result}"
                    ),
                }
            )

        typer.echo(
            "\n--- Evaluating ---"
        )

        evaluation = evaluator.evaluate()

        evaluation_ran = True

        typer.echo(
            f"Evaluation: {evaluation}"
        )

        recorder.record_step(
            {
                "type": "evaluation",
                "submitted": submitted,
                "content": evaluation,
            }
        )

    except Exception as exc:
        typer.echo(
            f"Run failed: {type(exc).__name__}: {exc}"
        )

        recorder.record_step(
            {
                "type": "runtime_error",
                "content": (
                    f"{type(exc).__name__}: {exc}"
                ),
            }
        )

        raise

    finally:
        typer.echo(
            "\n--- Saving Trajectory ---"
        )

        recorder.save(
            task_name=task,
        )

        typer.echo(
            "\n--- Tearing Down ---"
        )

        env.destroy()

        if evaluation_ran:
            typer.echo(
                "Run complete."
            )


if __name__ == "__main__":
    app()
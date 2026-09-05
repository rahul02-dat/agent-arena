import json
import time
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import typer

from arena.agents.agent import LLMAgent
from arena.core.types import ActionType, AgentRole
from arena.environments.docker import DockerEnvironment
from arena.evaluation.evaluator import get_evaluator
from arena.memory.local import LocalMemory
from arena.models.ollama import OllamaProvider
from arena.orchestration.sequential import SequentialOrchestrator
from arena.tools.terminal import TerminalTool
from arena.trajectories.recorder import TrajectoryRecorder


app = typer.Typer(
    help="Agent Arena CLI",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    pass


def resolve_task_dir(task_identifier: str) -> Path:
    direct = Path("tasks") / task_identifier
    if direct.is_dir() and (direct / "task.yaml").exists():
        return direct

    tasks_dir = Path("tasks")
    if tasks_dir.exists():
        for candidate in tasks_dir.iterdir():
            if candidate.is_dir() and (candidate / "task.yaml").exists():
                try:
                    with (candidate / "task.yaml").open("r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    if cfg and (cfg.get("id") == task_identifier or candidate.name == task_identifier):
                        return candidate
                except Exception:
                    continue

    raise FileNotFoundError(f"Task '{task_identifier}' not found in tasks/")


def build_agent_task_context(
    config: Dict[str, Any],
) -> Tuple[str, str]:
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
    task_arg: Optional[str] = typer.Argument(
        None,
        metavar="TASK",
        help="The name or ID of the task to run.",
    ),
    task_opt: Optional[str] = typer.Option(
        None,
        "--task",
        "-t",
        help="The name or ID of the task to run.",
    ),
    max_steps: Optional[int] = typer.Option(
        None,
        min=1,
        help="Maximum number of agent steps.",
    ),
    max_invalid_actions: int = typer.Option(
        3,
        min=1,
        help="Maximum consecutive invalid model actions.",
    ),
    force_build: bool = typer.Option(
        False,
        "--force-build",
        help="Force rebuild the Docker environment image.",
    ),
) -> None:
    task_identifier = task_opt or task_arg
    if not task_identifier:
        typer.echo("Error: Task must be specified via argument or --task option.")
        raise typer.Exit(code=1)

    typer.echo(f"Starting task: {task_identifier}")

    try:
        task_dir = resolve_task_dir(task_identifier)
    except FileNotFoundError as err:
        typer.echo(f"Error: {err}")
        raise typer.Exit(code=1)

    task_path = task_dir / "task.yaml"
    with task_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    task_id = config.get("id", task_identifier)
    task_name = config.get("name", task_identifier)
    task_version = config.get("version", "1.0")

    objective, task_instructions = build_agent_task_context(config)

    limits = config.get("limits", {})
    if max_steps is None:
        max_steps = limits.get("max_steps", 100)

    env_config = config.get("environment", {})
    network_setting = env_config.get("network", "disabled")
    cpus_setting = limits.get("cpus") or env_config.get("cpus")
    memory_setting = limits.get("memory_mb") or env_config.get("memory_mb")
    storage_setting = limits.get("storage_mb") or env_config.get("storage_mb")

    typer.echo(f"Loaded task: {task_name} (ID: {task_id}, v{task_version})")
    typer.echo(f"Objective: {objective}")

    model_config = config.get("model", {})
    model_name = model_config.get("name", "llama3.2")
    temperature = model_config.get("temperature", 0.0)

    recorder = TrajectoryRecorder(
        manifest={
            "task_id": task_id,
            "task_version": task_version,
            "model_name": model_name,
            "model_config": model_config,
            "agent_config": {
                "identity": "Agent-1",
                "role": AgentRole.EXECUTOR.value,
            },
            "orchestration_config": {
                "type": "sequential",
            },
            "limits": limits,
            "environment_config": env_config,
        }
    )

    env = DockerEnvironment(
        task_dir=str(task_dir),
        cpus=cpus_setting,
        memory_mb=memory_setting,
        storage_mb=storage_setting,
        network=network_setting,
    )

    submitted = False
    evaluation_ran = False
    failure_category = None
    failure_reason = None
    start_time = time.time()

    try:
        env.create(force_rebuild=force_build)

        model = OllamaProvider(
            model_name=model_name,
            temperature=temperature,
        )

        memory = LocalMemory()
        terminal_tool = TerminalTool(environment=env)

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

        orchestrator = SequentialOrchestrator(agents=[agent])
        evaluator = get_evaluator(environment=env, task_dir=task_dir)

        typer.echo("\n--- Starting Orchestrator Loop ---")

        initial_observation = env.observe()

        agent.observe(
            {
                "role": "user",
                "content": f"Initial environment observation:\n{initial_observation}",
            }
        )

        recorder.record_step(
            {
                "type": "observation",
                "content": initial_observation,
            },
            step=0,
            agent_id=agent.identity,
            agent_role=agent.role.value,
        )

        invalid_actions = 0

        for step in range(1, max_steps + 1):
            typer.echo(f"\nStep {step}:")

            action = orchestrator.next_action()
            typer.echo(f"Agent Action: {action}")

            recorder.record_step(
                {
                    "type": "action",
                    "content": action,
                },
                step=step,
                agent_id=agent.identity,
                agent_role=agent.role.value,
            )

            action_type = action.get("type")

            if action_type == "error":
                invalid_actions += 1
                feedback = (
                    f"Model/runtime error:\n{action.get('error')}\n"
                    "Try again using an available tool."
                )
                agent.observe({"role": "user", "content": feedback})
                if invalid_actions >= max_invalid_actions:
                    typer.echo("Too many invalid actions.")
                    failure_category = "AGENT_FAILURE"
                    failure_reason = "Exceeded maximum consecutive invalid model actions."
                    break
                continue

            if action_type == "invalid_action":
                invalid_actions += 1
                feedback = (
                    "Your previous response was not a valid tool call.\n"
                    f"Reason: {action.get('reason')}\n"
                    "Use one of the available tools and provide valid JSON arguments."
                )
                agent.observe({"role": "user", "content": feedback})
                recorder.record_step(
                    {
                        "type": "invalid_action",
                        "content": action,
                    },
                    step=step,
                    agent_id=agent.identity,
                    agent_role=agent.role.value,
                )
                if invalid_actions >= max_invalid_actions:
                    typer.echo("Too many invalid actions.")
                    failure_category = "AGENT_FAILURE"
                    failure_reason = "Exceeded maximum consecutive invalid model actions."
                    break
                continue

            if action_type == "duplicate_action":
                feedback = (
                    "Your previous proposed action is an exact duplicate "
                    "of the immediately preceding action. Do not repeat it "
                    "without new information. Choose a different action."
                )
                agent.observe({"role": "user", "content": feedback})
                recorder.record_step(
                    {
                        "type": "duplicate_action",
                        "content": action,
                    },
                    step=step,
                    agent_id=agent.identity,
                    agent_role=agent.role.value,
                )
                continue

            invalid_actions = 0
            tool_name = action.get("tool")
            arguments = action.get("arguments", {})

            # Submission handling via evaluator pre-submission validation
            if action_type == ActionType.SUBMIT.value or tool_name == "submit":
                reason = arguments.get("reason", "")

                if hasattr(evaluator, "validate_submission"):
                    is_valid, validation_error = evaluator.validate_submission()
                    if not is_valid:
                        typer.echo(f"Submission rejected: {validation_error}")
                        agent.observe(
                            {
                                "role": "user",
                                "content": (
                                    f"Submission rejected: {validation_error}. "
                                    "Continue working."
                                ),
                            }
                        )
                        continue

                submitted = True
                typer.echo(f"Agent submitted task: {reason}")
                recorder.record_step(
                    {
                        "type": "submission",
                        "content": {"reason": reason},
                    },
                    step=step,
                    agent_id=agent.identity,
                    agent_role=agent.role.value,
                )
                break

            tool = agent.tools.get(tool_name)
            if tool is None:
                agent.observe(
                    {
                        "role": "user",
                        "content": f"Tool {tool_name!r} is unavailable. Choose an available tool.",
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
                },
                step=step,
                agent_id=agent.identity,
                agent_role=agent.role.value,
            )

            tool_call_id = action.get("tool_call_id", f"call_{step}")

            agent.observe(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": arguments,
                            },
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

        typer.echo("\n--- Evaluating ---")
        evaluation = evaluator.evaluate()
        evaluation_ran = True

        typer.echo(f"Evaluation: {evaluation}")

        recorder.record_step(
            {
                "type": "evaluation",
                "submitted": submitted,
                "content": evaluation,
            },
            step=recorder.step_count + 1,
        )

        duration = time.time() - start_time

        if not submitted:
            failure_category = failure_category or "AGENT_TASK_FAILURE"
            failure_reason = failure_reason or "Max steps reached without valid submission."
        elif not evaluation.get("success"):
            failure_category = "AGENT_TASK_FAILURE"
            failure_reason = evaluation.get("failure_reason", "Evaluator rejected submitted artifact.")

        typer.echo(f"\nTask: {task_id}")
        typer.echo(f"Agent: {agent.identity} ({agent.role.value})")
        typer.echo(f"Model: {model_name}")

        if failure_category:
            typer.echo("\nStatus: FAILURE")
            typer.echo(f"Failure category: {failure_category}")
            typer.echo(f"Reason: {failure_reason}")
        else:
            typer.echo("\nStatus: SUCCESS")

        typer.echo(f"Reward: {evaluation.get('score', 0.0)}")
        typer.echo(f"Steps: {recorder.step_count}")
        typer.echo(f"Tool calls: {recorder.tool_call_count}")
        typer.echo(f"Duration: {duration:.2f}s")
        typer.echo(f"\nTrajectory:\n{recorder.file_path}")

    except Exception as exc:
        typer.echo(f"Run failed: {type(exc).__name__}: {exc}")
        recorder.record_step(
            {
                "type": "runtime_error",
                "content": f"{type(exc).__name__}: {exc}",
            },
            step=recorder.step_count + 1,
        )
        raise

    finally:
        typer.echo("\n--- Saving Trajectory ---")
        recorder.save(task_name=task_identifier)

        typer.echo("\n--- Tearing Down ---")
        env.destroy()

        if evaluation_ran:
            typer.echo("Run complete.")


if __name__ == "__main__":
    app()
import typer
import tomllib
from pathlib import Path
from arena.environments.docker import DockerEnvironment
from arena.models.ollama import OllamaProvider
from arena.agents.agent import LLMAgent
from arena.agents.roles import ROLES
from arena.core.types import AgentRole
from arena.memory.local import LocalMemory
from arena.tools.terminal import TerminalTool
from arena.evaluation.evaluator import Evaluator
from arena.trajectories.recorder import TrajectoryRecorder

app = typer.Typer(help="Agent Arena CLI", no_args_is_help=True)

@app.callback()
def main() -> None:
    pass

@app.command()
def run(task: str, max_steps: int = 5) -> None:
    typer.echo(f"Starting task: {task}")
    task_path = Path(f"tasks/{task}/task.yaml")
    
    if not task_path.exists():
        typer.echo(f"Error: Configuration not found at {task_path}")
        raise typer.Exit(code=1)
        
    with open(task_path, "rb") as f:
        config = tomllib.load(f)
    
    typer.echo(f"Loaded configuration for: {config.get('task', {}).get('name', 'Unknown')}")
    
    env = DockerEnvironment(task_dir=str(task_path.parent))
    env.create()
    
    model = OllamaProvider(model_name="llama3.2")
    memory = LocalMemory()
    terminal_tool = TerminalTool(environment=env)
    
    agent = LLMAgent(
        identity="Agent-1",
        role=AgentRole.EXPLORER,
        model=model,
        memory=memory,
        tools=[terminal_tool]
    )
    
    recorder = TrajectoryRecorder()
    evaluator = Evaluator(environment=env)
    
    typer.echo("\n--- Starting Orchestrator Loop ---")
    
    obs = env.observe()
    agent.observe(obs)
    recorder.record_step({"type": "observation", "content": obs})
    
    for step in range(1, max_steps + 1):
        typer.echo(f"\nStep {step}:")
        action = agent.act()
        typer.echo(f"Agent Action: {action}")
        recorder.record_step({"type": "action", "content": action})
        
        if action.get("error"):
            typer.echo(f"Error: {action['error']}")
            break
            
        if action.get("tool") == "terminal":
            command = action.get("command")
            if command:
                res = terminal_tool.execute(command=command)
                agent.observe(res)
                recorder.record_step({"type": "tool_result", "content": res})
            else:
                break
        else:
            break
            
    typer.echo("\n--- Evaluating ---")
    eval_res = evaluator.evaluate()
    typer.echo(f"Evaluation: {eval_res}")
    recorder.record_step({"type": "evaluation", "content": eval_res})
    
    typer.echo("\n--- Saving Trajectory ---")
    recorder.save(task_name=task)
        
    typer.echo("\n--- Tearing Down ---")
    env.destroy()
    typer.echo("Run complete.")

if __name__ == "__main__":
    app()

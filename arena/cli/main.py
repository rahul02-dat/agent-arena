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

app = typer.Typer(help="Agent Arena CLI", no_args_is_help=True)

@app.callback()
def main() -> None:
    pass

@app.command()
def run(task: str) -> None:
    typer.echo(f"Starting task: {task}")
    task_path = Path(f"tasks/{task}/task.yaml")
    
    if not task_path.exists():
        typer.echo(f"Error: Configuration not found at {task_path}")
        raise typer.Exit(code=1)
        
    with open(task_path, "rb") as f:
        config = tomllib.load(f)
    
    typer.echo(f"Loaded configuration for: {config.get('task', {}).get('name', 'Unknown')}")
    
    env = DockerEnvironment()
    env.create()
    
    model = OllamaProvider(model_name="llama3")
    memory = LocalMemory()
    terminal_tool = TerminalTool()
    
    agent = LLMAgent(
        identity="Agent-1",
        role=AgentRole.EXPLORER,
        model=model,
        memory=memory,
        tools=[terminal_tool]
    )
    
    typer.echo("\n--- Starting Orchestrator Loop ---")
    for step in range(1, 4):
        typer.echo(f"\nStep {step}:")
        obs = env.observe()
        agent.observe(obs)
        action = agent.act()
        typer.echo(f"Agent Action: {action}")
        env.execute(action)
        
    typer.echo("\n--- Tearing Down ---")
    env.destroy()
    typer.echo("Run complete.")

if __name__ == "__main__":
    app()

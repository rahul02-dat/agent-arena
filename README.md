# Agent Arena

Agent Arena is a research platform for studying autonomous AI agents operating inside realistic terminal environments.

## Research Question
> Can reinforcement learning learn effective orchestration policies for teams of autonomous language-model agents operating in complex, partially observable terminal environments?

## Architecture Overview
The platform isolates environments (via Docker) from the agent reasoning loop. Agents are instantiated with specific roles and tools (such as the `TerminalTool`), allowing them to observe the environment, communicate, and take action. A central orchestrator governs the multi-agent interactions, and trajectories are recorded for offline reinforcement learning and evaluation.

## Installation
The project uses `pyproject.toml` for standard dependency management and requires Python 3.12+.
Local Ollama is the default model runtime.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

To install development dependencies (like `pytest`):
```bash
pip install -e ".[dev]"
```

## Quickstart
After installing, you can run the primary CLI to execute a task environment:

```bash
arena run --task <task_id>
```

Example:
```bash
arena run --task ecdsa_nonce_bias_001
```

## Documentation
For more detailed information, see the documents in the `docs/` directory:
- Architecture
- Agents
- Environments
- Evaluation
- Trajectories

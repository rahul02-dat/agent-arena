# Agent Arena

Agent Arena is a research platform for studying autonomous AI agents operating inside realistic, isolated terminal environments.

## Research Question
> Can reinforcement learning learn effective orchestration policies for teams of autonomous language-model agents operating in complex, partially observable terminal environments?

## Architecture Principles

Agent Arena enforces strict architectural separation between core concepts:

```text
Model → Agent → Tool → Environment → Observation → Action → Memory → Orchestrator → Evaluator → Trajectory
```

- **Docker Isolation**: Every agent interaction executes inside an isolated Docker container with enforced resource limits (CPU, memory, storage) and network policies (`disabled`, `isolated`, `allowed`). Hard execution timeouts and output limits are enforced on all tool invocations.
- **Trusted Host Evaluator**: The evaluator operates entirely on the host side. Ground truth secrets and test suites are **never** mounted or copied into the agent container.
- **Pre-Submission Artifact Validation**: The evaluator validates the format and scalar range of generated artifacts prior to submission acceptance, providing structured feedback and preventing empty or trivial submissions.
- **Structured Trajectories & Manifests**: Every step is validated against typed Pydantic schemas and logged as JSONL in `results/<experiment_id>/episodes/<episode_id>.jsonl`. A research manifest (`manifest.json`) records exact model configurations, task versions, seeds, and resource limits.

---

## Directory Structure

```text
├── arena/                     # Core Agent Arena platform
│   ├── agents/                # Agent abstractions and role definitions
│   ├── cli/                   # Typer CLI entrypoint (`arena`)
│   ├── core/                  # Types, protocols, and errors
│   ├── environments/          # Docker and execution environments
│   ├── evaluation/            # Base evaluator and dynamic loader
│   ├── models/                # LLM provider abstractions (e.g. Ollama)
│   ├── orchestration/         # Multi-agent orchestrators (e.g. Sequential)
│   ├── tools/                 # Tool implementations (e.g. TerminalTool)
│   └── trajectories/          # Typed schemas and JSONL recorder
├── tasks/                     # Benchmark tasks
│   └── ecdsa_nonce_bias_001/  # ECDSA Nonce Bias Recovery task
│       ├── task.yaml          # Task configuration, limits, and objectives
│       ├── environment/       # Dockerfile and public signatures dataset
│       ├── evaluator/         # Host-side trusted evaluator
│       └── reference/         # Reference solver and protected ground truth
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests (config, registry, actions, trajectories, evaluator)
│   └── integration/           # Docker isolation and mock agent integration tests
└── docs/                      # Research papers and platform documentation
```

---

## Installation

Agent Arena requires Python 3.12+ and Docker.

Using `uv` (recommended):
```bash
# Clone the repository
git clone https://github.com/rahul02-dat/cryptography.git
cd cryptography

# Install dependencies and arena CLI in editable mode
uv sync
```

Or using standard `venv` and `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Quickstart

Ensure Docker is running, then run a task via the CLI:

```bash
arena run --task ecdsa_nonce_bias_001
```

Or using positional argument:
```bash
arena run ecdsa_nonce_bias_001
```

### CLI Options

```text
Usage: arena run [OPTIONS] [TASK]

Arguments:
  TASK                        The task ID or directory name (e.g. ecdsa_nonce_bias_001)

Options:
  -t, --task TEXT             The task ID or directory name
  --max-steps INTEGER         Override max agent steps from task configuration
  --max-invalid-actions INT   Max consecutive invalid model actions before aborting [default: 3]
  --force-build               Force rebuild of the Docker environment image
  --help                      Show CLI options and exit
```

---

## Benchmark: ECDSA Nonce Bias Recovery (`ecdsa_nonce_bias_001`)

The initial benchmark tasks an autonomous agent with recovering a secp256k1 private key from a biased-nonce signature dataset (`/app/data/signatures.json`).

- **Artifact**: The agent must inspect the dataset, formulate the linear Hidden Number Problem (HNP), construct a lattice embedding, run lattice reduction (LLL/BKZ), and output the recovered private key as a hexadecimal integer to `/app/private_key.txt`.
- **Pre-Submission Validation**: The runtime checks that `/app/private_key.txt` exists, is non-empty, contains valid hexadecimal, and represents a scalar $0 < d < N$.
- **Protected Evaluation**: The host evaluator independently verifies that:
  1. $d == d_{\text{expected}}$ against protected ground truth.
  2. $d \cdot G == Q$ reproduces the disclosed public key on the secp256k1 curve.

---

## Running Tests

Run the full test suite (29 tests):

```bash
uv run pytest -v
```

Run unit tests only:
```bash
uv run pytest tests/unit -v
```

Run Docker integration tests (requires Docker daemon running):
```bash
uv run pytest tests/integration -v
```

---

## Documentation

For background on the research architecture and reinforcement learning roadmap, see the [Agent Arena Research Platform Specification](docs/agent_arena_research_platform.md) (or the [original PDF](docs/Agent%20Arena%20Research%20Platform.pdf)) in the `docs/` directory.


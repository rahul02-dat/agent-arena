# AGENTS.md

# Agent Arena

## Project-Level Engineering and Research Specification

**Project status:** Early research / greenfield implementation  
**Primary language:** Python  
**Primary model runtime:** Ollama  
**Primary development environment:** Apple Silicon, local-first  
**Budget constraint:** Zero paid infrastructure  
**Primary objective:** Research-grade platform for autonomous terminal agents, multi-agent collaboration, and reinforcement-learning-based orchestration.

---

# 1. Purpose of This File

This file is the authoritative engineering specification for the Agent Arena repository.

Any human or AI agent modifying this repository MUST follow the rules defined here.

The purpose of this file is to prevent:

- architectural drift;
- unnecessary dependencies;
- premature abstraction;
- cloud-service dependencies;
- benchmark leakage;
- evaluator contamination;
- reward hacking;
- accidental coupling between agents and environments;
- uncontrolled changes to experimental conditions;
- mixing research infrastructure with task-specific implementations.

When another document conflicts with this file, this file takes precedence unless a newer explicit project-level decision supersedes it.

---

# 2. Project Definition

Agent Arena is a research platform for studying autonomous AI agents operating inside realistic terminal environments.

The core research question is:

> Can reinforcement learning learn effective orchestration policies for teams of autonomous language-model agents operating in complex, partially observable terminal environments?

The platform must support:

1. Single-agent terminal environments.
2. Multi-agent terminal environments.
3. Role-specialized agents.
4. Agent-to-agent communication.
5. Shared and private memory.
6. Environment isolation.
7. Deterministic evaluation.
8. Trajectory recording.
9. Fine-grained reward computation.
10. Learned orchestration.
11. Reinforcement-learning experiments.
12. Reproducible research experiments.

The project is NOT initially:

- a commercial SaaS product;
- a cloud agent platform;
- a generic chatbot framework;
- a LangChain replacement;
- a model-training platform;
- a benchmark consisting only of static questions;
- a collection of coding puzzles.

---

# 3. Core Research Philosophy

The project must treat the following as separate concepts:

```text
Model
Agent
Tool
Environment
Observation
Action
Memory
Communication
Orchestrator
Evaluator
Reward
Trajectory
Experiment
```

Never collapse these concepts into one abstraction.

The architecture must allow:

```text
Model A + Agent Role X
Model A + Agent Role Y
Model B + Agent Role X
Model B + Agent Role Y
```

without changing the environment or evaluator.

The architecture must also allow:

```text
Single agent
Multi-agent
Static orchestration
LLM orchestration
RL orchestration
```

without rewriting task environments.

---

# 4. Non-Negotiable Constraints

## 4.1 Zero Paid Infrastructure

The project must be usable without:

- paid API keys;
- paid cloud GPUs;
- paid databases;
- paid observability;
- paid experiment tracking;
- paid hosted vector databases;
- paid inference APIs.

Local Ollama is the default model runtime.

The project must not require internet access during an experiment unless a task explicitly declares network access as part of the environment.

---

## 4.2 Local-First

The primary development target is a local Apple Silicon machine with approximately 24 GB unified memory.

The architecture must not assume:

- CUDA;
- NVIDIA GPUs;
- distributed clusters;
- cloud execution;
- Kubernetes.

CUDA-specific functionality may be added later, but it must never be a hard dependency of the core platform.

---

## 4.3 Reproducibility

Every experiment must be reproducible as far as technically possible.

An experiment must record:

- task ID;
- task version;
- environment version;
- model name;
- model configuration;
- agent configuration;
- orchestration configuration;
- random seed;
- resource limits;
- evaluator version;
- reward configuration;
- software version;
- timestamp.

Do not change experimental parameters silently.

---

## 4.4 Evaluator Isolation

The agent MUST NOT have access to:

- ground truth;
- hidden evaluator state;
- evaluator implementation when it exposes protected information;
- private test fixtures;
- reference solutions;
- scoring internals that could be exploited.

The evaluator must operate outside the agent-controlled environment whenever practical.

---

## 4.5 No Reward Leakage

Reward information must not expose the solution.

The agent may receive legitimate progress feedback.

It must not receive:

```text
"The private key is X"
"The correct file is Y"
"The expected command is Z"
```

unless that information is legitimately observable in the task.

---

# 5. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │        Task         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Environment     │
                         │       Docker        │
                         └──────────┬──────────┘
                                    │
                               observations
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Agent Runtime    │
                         └──────────┬──────────┘
                                    │
                      ┌─────────────┼─────────────┐
                      │             │             │
                      ▼             ▼             ▼
                   Explorer      Researcher    Executor
                      │             │             │
                      └─────────────┼─────────────┘
                                    │
                              communication
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Orchestrator     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                              Environment
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Evaluator       │
                         └──────────┬──────────┘
                                    │
                              reward / metrics
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Trajectory      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Research / RL     │
                         └─────────────────────┘
```

---

# 6. Required Repository Structure

The repository MUST begin with this structure:

```text
agent-arena/
│
├── AGENTS.md
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
│
├── arena/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── errors.py
│   │   ├── config.py
│   │   └── protocols.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── agent.py
│   │   └── roles.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── ollama.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   └── terminal.py
│   │
│   ├── environments/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── docker.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── local.py
│   │
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── messages.py
│   │   └── bus.py
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── sequential.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── evaluator.py
│   │   ├── rewards.py
│   │   └── metrics.py
│   │
│   ├── trajectories/
│   │   ├── __init__.py
│   │   ├── recorder.py
│   │   └── schema.py
│   │
│   └── cli/
│       ├── __init__.py
│       └── main.py
│
├── tasks/
│   └── ecdsa_nonce_bias/
│       ├── task.yaml
│       ├── README.md
│       ├── environment/
│       │   ├── Dockerfile
│       │   ├── setup.sh
│       │   └── app/
│       ├── evaluator/
│       │   ├── evaluator.py
│       │   └── tests/
│       └── reference/
│
├── experiments/
│   └── README.md
│
├── results/
│   └── .gitkeep
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/
│   └── README.md
│
└── docs/
    ├── architecture.md
    ├── agents.md
    ├── environments.md
    ├── evaluation.md
    ├── trajectories.md
    ├── multi_agent.md
    └── reinforcement_learning.md
```

---

# 7. File-by-File Specification

# 7.1 `AGENTS.md`

## Purpose

Authoritative engineering instructions.

## MAY contain

- architecture;
- project rules;
- file ownership;
- implementation constraints;
- research principles;
- testing requirements;
- security rules.

## MUST NOT contain

- runtime logic;
- secrets;
- API keys;
- experiment results;
- generated trajectories;
- task ground truth.

---

# 7.2 `README.md`

## Purpose

Public project introduction.

## MUST contain

- project description;
- research question;
- architecture overview;
- installation instructions;
- quickstart;
- development status;
- basic usage;
- links to detailed documentation.

## MAY contain

- diagrams;
- benchmark results after publication;
- screenshots;
- examples.

## MUST NOT contain

- hidden evaluator details;
- task ground truth;
- credentials;
- private research notes;
- temporary debugging instructions.

The README is public-facing.

---

# 7.3 `LICENSE`

Contains the project license.

The license must be chosen explicitly.

Do not copy a license from another project without verifying its compatibility.

---

# 7.4 `pyproject.toml`

## Purpose

Single source of truth for Python package metadata and dependencies.

## MUST contain

- package metadata;
- supported Python version;
- dependencies;
- development dependencies;
- CLI entry point;
- tool configuration where appropriate.

## Initial dependency philosophy

Keep dependencies minimal.

Initial expected dependencies include:

```text
ollama
pydantic
typer
docker
gymnasium
pettingzoo
pytest
```

Additional dependencies must have a documented reason.

Do NOT add:

- LangChain;
- LangGraph;
- cloud SDKs;
- database servers;
- distributed frameworks;

unless the project explicitly reaches the stage requiring them.

---

# 7.5 `.gitignore`

Must ignore:

```text
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
.env
*.log

results/*
!results/.gitkeep

models/
checkpoints/
artifacts/
```

Do not ignore source code, task specifications, evaluator code, or reproducibility metadata.

---

# 8. `arena/core/`

This package contains foundational data structures and contracts.

It must remain dependency-light.

---

# 8.1 `arena/core/types.py`

## Purpose

Shared typed data structures.

May contain:

- enums;
- identifiers;
- immutable value objects;
- primitive domain types.

Examples:

```text
AgentId
TaskId
EpisodeId
ActionType
AgentRole
EpisodeStatus
```

Must NOT contain:

- Ollama calls;
- Docker calls;
- reward logic;
- model-specific code;
- terminal execution.

---

# 8.2 `arena/core/errors.py`

Contains project-specific exceptions.

Examples:

```text
ArenaError
EnvironmentError
AgentError
ToolError
EvaluationError
ConfigurationError
TrajectoryError
```

Must NOT contain operational logic.

---

# 8.3 `arena/core/config.py`

Contains validated configuration models.

Use Pydantic.

Examples:

```text
ArenaConfig
AgentConfig
ModelConfig
EnvironmentConfig
EvaluationConfig
ExperimentConfig
```

Configuration should be data, not behavior.

---

# 8.4 `arena/core/protocols.py`

Contains Python `Protocol` definitions for major interfaces.

Expected interfaces:

```text
LLMProvider
Agent
Environment
Tool
Memory
Evaluator
Orchestrator
TrajectoryRecorder
```

The purpose is dependency inversion.

Implementations must depend on interfaces rather than the reverse.

---

# 9. `arena/models/`

This package contains model-runtime integrations.

---

# 9.1 `arena/models/base.py`

Defines the model abstraction.

Conceptually:

```text
LLMProvider
    ↓
chat()
generate()
```

The interface must not assume Ollama.

It should represent generic model interaction.

---

# 9.2 `arena/models/ollama.py`

Contains the Ollama implementation.

Ollama exposes a local API at:

```text
http://localhost:11434/api
```

when running locally. Its chat API supports tool calls, and its Python library can pass functions as tools.

This file MAY contain:

- Ollama client initialization;
- model requests;
- tool-call parsing;
- response normalization;
- usage metadata.

This file MUST NOT contain:

- agent roles;
- task logic;
- reward logic;
- evaluator logic;
- orchestration logic.

The rest of the application must communicate through `LLMProvider`, not directly through Ollama.

---

# 10. `arena/agents/`

Contains agent behavior.

---

# 10.1 `arena/agents/base.py`

Defines the conceptual agent interface.

An agent must have:

```text
identity
role
model
tools
memory
observe()
act()
```

The base class must not know about a specific task.

---

# 10.2 `arena/agents/agent.py`

Contains the default LLM-driven agent implementation.

The agent loop should conceptually be:

```text
observe
   ↓
construct context
   ↓
call model
   ↓
parse action/tool call
   ↓
execute tool
   ↓
record result
   ↓
repeat
```

Ollama explicitly supports multi-turn tool-calling loops, so the implementation should use structured tool calls rather than asking models to emit arbitrary shell syntax when practical.

The agent must never directly manipulate Docker internals.

---

# 10.3 `arena/agents/roles.py`

Defines role metadata.

Initial roles:

```text
EXPLORER
RESEARCHER
EXECUTOR
CRITIC
VERIFIER
ORCHESTRATOR
```

Role definitions should describe responsibilities and constraints.

They must not contain task-specific solutions.

---

# 11. `arena/tools/`

Contains capabilities available to agents.

---

# 11.1 `arena/tools/base.py`

Defines the generic tool interface.

A tool must specify:

```text
name
description
input schema
output schema
execute()
```

Tools should be deterministic where practical.

---

# 11.2 `arena/tools/registry.py`

Contains tool registration and lookup.

The registry must prevent arbitrary tool execution unless explicitly registered.

---

# 11.3 `arena/tools/terminal.py`

Defines the terminal tool exposed to agents.

The terminal tool must execute commands INSIDE the task environment.

It must NOT execute arbitrary agent-generated commands directly on the host machine.

The host shell is never an implicit agent tool.

---

# 12. `arena/environments/`

Contains environment abstractions and Docker implementations.

---

# 12.1 `arena/environments/base.py`

Defines the generic environment interface.

Required conceptual operations:

```text
create()
reset()
observe()
execute()
snapshot()
destroy()
```

The environment abstraction must not contain task-specific logic.

---

# 12.2 `arena/environments/docker.py`

Contains Docker-backed environment implementation.

Docker is the default isolation mechanism.

The implementation may manage:

- image creation;
- container lifecycle;
- mounts;
- environment variables;
- resource limits;
- networking;
- command execution;
- cleanup.

It must not contain:

- evaluator scoring;
- agent prompts;
- task-specific solutions.

Docker's purpose is to provide an isolated, reproducible runtime environment.

---

# 13. `arena/memory/`

Contains agent memory.

---

# 13.1 `arena/memory/base.py`

Defines memory interface.

Memory should support:

```text
write()
read()
search()
clear()
```

---

# 13.2 `arena/memory/local.py`

Initial local implementation.

Use simple local structures/files.

Do NOT introduce a vector database.

Do NOT introduce embeddings unless a demonstrated research requirement appears.

Memory must preserve provenance where practical.

---

# 14. `arena/communication/`

Contains inter-agent communication.

---

# 14.1 `arena/communication/messages.py`

Defines message schema.

Messages should include:

```text
message_id
sender
recipient
timestamp
message_type
content
metadata
```

Message types may include:

```text
FACT
HYPOTHESIS
REQUEST
RESULT
WARNING
CRITIQUE
DECISION
```

---

# 14.2 `arena/communication/bus.py`

Defines the communication mechanism.

Initial implementation should be in-process.

Do NOT add Redis or a message broker.

Communication must be recordable as part of the trajectory.

---

# 15. `arena/orchestration/`

Contains policies controlling agent coordination.

---

# 15.1 `arena/orchestration/base.py`

Defines the orchestrator interface.

An orchestrator chooses actions such as:

```text
SELECT_AGENT
DELEGATE
REQUEST_REVIEW
REQUEST_VERIFICATION
RETRY
STOP
```

The orchestrator must not directly implement environment-specific solutions.

---

# 15.2 `arena/orchestration/sequential.py`

Initial deterministic orchestration strategy.

Example:

```text
Explorer
→ Researcher
→ Executor
→ Critic
→ Verifier
```

This is the baseline against which learned orchestration will eventually be compared.

Do not implement RL here.

---

# 16. `arena/evaluation/`

This package is one of the most security-sensitive parts of the project.

---

# 16.1 `arena/evaluation/evaluator.py`

Defines the evaluator interface.

The evaluator receives:

```text
task
final environment state
protected evaluation data
```

and produces:

```text
success
score
metrics
failure reason
```

The evaluator should be independent from agent reasoning.

---

# 16.2 `arena/evaluation/rewards.py`

Contains reward calculations.

Reward components may include:

```text
task success
progress
information gain
recovery
efficiency
communication cost
wasted actions
unsafe actions
```

Reward logic must be versioned.

Do not silently modify reward coefficients during experiments.

---

# 16.3 `arena/evaluation/metrics.py`

Contains non-training metrics.

Examples:

```text
success_rate
episode_length
tool_calls
token_usage
wall_time
recovery_rate
communication_count
communication_cost
unsafe_actions
```

Metrics and rewards are separate concepts.

A metric may be reported without being part of the reward.

---

# 17. `arena/trajectories/`

Contains trajectory recording.

---

# 17.1 `arena/trajectories/schema.py`

Defines Pydantic schemas for:

```text
Episode
TrajectoryStep
Observation
Action
ToolCall
ToolResult
Message
RewardEvent
EvaluationResult
```

Schemas must be stable.

Breaking changes require versioning.

---

# 17.2 `arena/trajectories/recorder.py`

Records execution events.

Every meaningful interaction should be recordable:

```text
agent action
tool call
tool result
agent message
environment event
reward
evaluation
```

The recorder must not alter agent behavior.

Recording should be observational.

---

# 18. `arena/cli/`

Contains command-line interfaces.

---

# 18.1 `arena/cli/main.py`

The CLI should eventually support:

```text
arena task list
arena task validate
arena env build
arena env reset
arena run
arena evaluate
arena analyze
arena experiment
arena replay
```

Do not implement every command initially.

Implement only commands backed by working functionality.

---

# 19. `tasks/`

This directory contains benchmark tasks.

A task is an environment specification, not an agent implementation.

Each task must be independently runnable.

---

# 19.1 Task Directory Structure

Each task should follow:

```text
tasks/<task_id>/
├── task.yaml
├── README.md
├── environment/
├── evaluator/
└── reference/
```

---

# 19.2 `task.yaml`

Contains task metadata.

Example:

```yaml
id: ecdsa_nonce_bias_001
version: "1.0"

name: ECDSA Nonce Bias Recovery

category: cryptography
difficulty: expert

objective:
  type: state_change
  description: Recover and verify the target private key.

environment:
  runtime: docker
  network: disabled

limits:
  max_steps: 500
  timeout_seconds: 1200

agents:
  max_agents: 5
  communication: true
  partial_observability: true

evaluation:
  correctness: true
  efficiency: true
  safety: true
```

The task specification must describe the task without exposing hidden ground truth.

---

# 19.3 `tasks/<task>/README.md`

Public task documentation.

Must explain:

- task purpose;
- user-facing objective;
- environment;
- expected interaction;
- constraints;
- how to run the task;
- evaluation at a high level.

Must NOT expose:

- private ground truth;
- hidden test data;
- reference solution;
- evaluator weaknesses.

---

# 20. Task Environment

The environment contains everything the agent is legitimately allowed to interact with.

It may contain:

- source code;
- logs;
- datasets;
- services;
- configuration;
- binaries;
- intentionally broken components.

It must NOT contain:

- ground-truth private keys;
- evaluator secrets;
- reference solution files;
- scoring internals;
- host credentials.

---

# 21. Task Dockerfile

Each environment must be independently buildable.

The Dockerfile may contain:

- OS base image;
- system dependencies;
- Python dependencies;
- application files;
- task data;
- startup configuration.

The Dockerfile must NOT contain:

- host secrets;
- evaluator credentials;
- private benchmark keys;
- external service credentials.

Pin versions where reproducibility requires it.

---

# 22. `tasks/<task>/evaluator/`

The evaluator is trusted infrastructure.

It must be logically separated from the agent environment.

Evaluator code may contain:

- ground truth;
- protected tests;
- correctness checks;
- scoring logic.

Evaluator code must NEVER be copied into the agent's environment.

---

# 23. `tasks/<task>/reference/`

Contains trusted reference material.

May contain:

- reference solution;
- expected output;
- validation artifacts;
- researcher-only notes.

This directory is never mounted into the agent container.

Reference material must never be included in public task artifacts unless intentionally released.

---

# 24. Initial ECDSA Task

The first environment is based on the existing cryptography challenge.

The task involves recovering an ECDSA private key from biased nonces using cryptanalytic techniques.

The environment is valuable because it requires:

```text
repository exploration
+
cryptographic reasoning
+
mathematical reasoning
+
code execution
+
experimentation
+
debugging
+
verification
```

The initial implementation should preserve the original challenge's difficulty.

Do not simplify it merely to make the first agent succeed.

---

# 25. `experiments/`

This directory contains experiment configurations and research notes.

It must NOT contain source code that belongs in `arena/`.

An experiment should specify:

```text
task
model
agent configuration
orchestration strategy
reward configuration
random seed
resource limits
```

Experiment configurations should be immutable once published.

If a configuration changes materially, create a new experiment version.

---

# 26. `results/`

Runtime output only.

This directory should contain:

```text
experiment/
    config.json
    episodes/
    metrics.json
    summary.json
```

Results should generally not be committed to the repository.

Large trajectories must not be committed.

---

# 27. `tests/`

Tests are mandatory.

---

# 27.1 `tests/unit/`

Test individual components.

Examples:

```text
test_config.py
test_messages.py
test_trajectory.py
test_tools.py
test_rewards.py
test_agent.py
```

Unit tests must not require Ollama or Docker unless explicitly marked as integration tests.

---

# 27.2 `tests/integration/`

Tests:

- Ollama integration;
- Docker environment;
- agent/tool interaction;
- evaluator integration;
- complete episode execution.

Integration tests may require local infrastructure.

---

# 27.3 `tests/fixtures/`

Contains safe deterministic test fixtures.

Do not place production benchmark secrets here.

---

# 28. `scripts/`

Contains temporary or operational utilities.

Scripts must not become the primary application interface.

If a script becomes essential functionality, move the logic into `arena/` and make the script a thin wrapper.

---

# 29. `docs/`

Documentation must explain architecture rather than duplicate implementation details unnecessarily.

Required documents:

```text
architecture.md
agents.md
environments.md
evaluation.md
trajectories.md
multi_agent.md
reinforcement_learning.md
```

---

# 30. Gymnasium Integration

Gymnasium is the standard single-agent RL environment interface.

Custom environments should follow Gymnasium's environment model, including explicit observation and action spaces, reset/step semantics, and proper termination/truncation handling.

The Agent Arena environment abstraction may wrap Gymnasium rather than exposing Gymnasium directly to every component.

Do not force LLM agents to emit raw Gymnasium actions.

LLM actions should first pass through the Agent Arena action abstraction.

---

# 31. PettingZoo Integration

PettingZoo is the standard multi-agent RL interface for this project.

PettingZoo supports both:

- Agent Environment Cycle (AEC);
- Parallel API.

The project should initially use the API that best matches sequential agent orchestration.

PettingZoo should be integrated at the RL/environment boundary.

The agent runtime should not depend directly on PettingZoo-specific internals.

---

# 32. Ollama Integration

Ollama is the default local LLM provider.

Local API:

```text
http://localhost:11434/api
```

Local access does not require authentication.

The implementation should prefer structured chat/tool calling.

Ollama supports tool calling and multi-turn agent loops.

Model/runtime usage metrics should be captured when available.

Ollama exposes metrics such as:

```text
total_duration
load_duration
prompt_eval_count
prompt_eval_duration
eval_count
eval_duration
```

These should be stored as trajectory metadata when available.

---

# 33. Tool Calling Rules

Agents should use structured tool calls.

Preferred:

```text
Model
 ↓
Tool call
 ↓
Tool executor
 ↓
Tool result
 ↓
Model
```

Avoid relying on fragile natural-language parsing such as:

```text
RUN_COMMAND: ls -la
```

when structured tool calling can represent the same action.

The tool layer must validate arguments before execution.

---

# 34. Terminal Security

The terminal is the highest-risk tool.

The agent must NEVER receive unrestricted host shell access.

Commands must execute inside the task environment.

The implementation must enforce:

- container boundaries;
- execution timeout;
- output limits;
- process limits where practical;
- filesystem boundaries;
- network policy;
- cleanup.

The terminal tool must record:

```text
command
start time
end time
exit code
stdout
stderr
resource metadata
```

---

# 35. Agent Roles

Initial roles:

## Explorer

Objective:

> Maximize useful environmental information.

May:

- inspect files;
- inspect logs;
- inspect processes;
- inspect configuration;
- run read-only diagnostics.

Should avoid unnecessary modifications.

---

## Researcher

Objective:

> Develop technically justified hypotheses and solution strategies.

May:

- reason about algorithms;
- analyze evidence;
- suggest experiments;
- inspect information provided by the orchestrator.

Should not be assumed to have unrestricted environment access.

---

## Executor

Objective:

> Implement and test proposed solutions.

May:

- write code;
- execute experiments;
- install permitted dependencies;
- run tests.

---

## Critic

Objective:

> Find weaknesses in the proposed solution.

Should actively search for:

- invalid assumptions;
- incomplete solutions;
- hidden failure cases;
- regressions.

---

## Verifier

Objective:

> Independently determine whether the task is solved.

The verifier should have an information path that reduces confirmation bias.

---

## Orchestrator

Objective:

> Allocate agent actions efficiently.

Possible actions:

```text
SELECT_AGENT
REQUEST_INFORMATION
DELEGATE
REQUEST_REVIEW
REQUEST_VERIFICATION
RETRY
STOP
```

---

# 36. Multi-Agent Rules

Multi-agent behavior must be measurable.

Every agent interaction must be recordable.

The system must track:

```text
agent identity
role
observation
action
message
recipient
timestamp
reward
result
```

Do not create agents merely for visual complexity.

Every additional agent must have a measurable purpose.

---

# 37. Agent Count

The initial system should support:

```text
1 agent
2 agents
3 agents
5 agents
```

The default research configuration should begin with three:

```text
Explorer
Researcher
Executor
```

Critic and Verifier should be introduced afterward.

Do not assume more agents means better performance.

---

# 38. Model Assignment

Model assignment must be configurable.

Example:

```yaml
agents:
  explorer:
    model: local-8b

  researcher:
    model: local-14b

  executor:
    model: local-8b
```

Do not hard-code model names into role implementations.

This allows experiments such as:

```text
single 14B
```

versus:

```text
8B + 14B + 8B
```

---

# 39. Resource Constraints

Experiments should support:

```text
max_episode_steps
max_wall_time
max_tool_calls
max_model_tokens
max_communication_messages
```

Resource limits must be enforced by infrastructure, not merely described in prompts.

---

# 40. Memory Rules

Agent memory must distinguish:

```text
short-term context
persistent memory
shared memory
private memory
```

Do not blindly append the entire episode history to every prompt.

Long histories must eventually be summarized or selectively retrieved.

Memory retrieval must be logged.

---

# 41. Reward Design

The reward system must distinguish:

```text
task outcome
progress
efficiency
recovery
safety
communication
```

Do not optimize for command count alone.

Do not optimize for token count alone.

Do not reward textual explanations unless they correspond to verifiable progress.

---

# 42. Reward Hacking Prevention

The following behaviors must not generate legitimate positive reward:

- creating fake progress files;
- modifying evaluator code;
- modifying protected tests;
- generating huge amounts of output;
- repeatedly running commands without information gain;
- exploiting known evaluator weaknesses;
- discovering hidden ground truth through filesystem traversal.

The evaluator must validate actual state rather than trusting agent claims.

---

# 43. Trajectory Schema

Each trajectory step should conceptually contain:

```json
{
  "episode_id": "...",
  "step": 12,
  "agent_id": "executor",
  "observation": {},
  "action": {},
  "tool_calls": [],
  "messages": [],
  "result": {},
  "reward": 0.05,
  "timestamp": "...",
  "metadata": {}
}
```

The schema must be versioned.

---

# 44. Experiment Reproducibility

Every experiment must produce:

```text
config.json
environment metadata
model metadata
trajectory files
metrics
evaluation result
```

An experiment must be identifiable without relying on directory naming conventions alone.

Use stable IDs.

---

# 45. Research Baselines

Every new multi-agent method must be compared against at least:

```text
Baseline 1:
Single generalist agent

Baseline 2:
Static multi-agent workflow
```

When evaluating RL orchestration, also compare against:

```text
Baseline 3:
Non-learned orchestrator
```

Do not report only the best-performing architecture.

---

# 46. Mandatory Experimental Metrics

At minimum:

```text
success_rate
mean_reward
median_reward
episode_length
tool_calls
wall_time
model_tokens
communication_count
communication_tokens
recovery_rate
unsafe_action_count
```

Additional metrics may be added per task.

---

# 47. Collaboration Metrics

Define:

```text
multi_agent_gain
communication_efficiency
cost_adjusted_success
```

For example:

\[
MultiAgentGain =
Success_{multi} - Success_{single}
\]

and:

\[
CostAdjustedSuccess =
\frac{Success}{ComputeCost}
\]

Do not claim multi-agent superiority without accounting for increased computation.

---

# 48. Reinforcement Learning

RL is NOT part of the first implementation milestone.

First establish:

```text
environment
single agent
multi-agent
evaluation
trajectory recording
```

Only then introduce RL.

The first RL target should be the orchestrator.

Do NOT initially RL-train the underlying LLM.

---

# 49. Initial RL Action Space

The first learned orchestrator may choose:

```text
EXPLORER
RESEARCHER
EXECUTOR
CRITIC
VERIFIER
STOP
```

The policy should learn:

> Who should act next?

before attempting to learn:

> What should the LLM think?

This keeps the first RL problem computationally manageable.

---

# 50. RL State Representation

The initial orchestrator state may include:

```text
task difficulty
current progress
agent confidence
recent failures
last action
episode length
remaining budget
communication count
verification status
```

Do not include hidden ground truth.

---

# 51. Curriculum Learning

Tasks should eventually be organized by difficulty.

Possible progression:

```text
Level 1
Deterministic debugging

Level 2
Multi-file debugging

Level 3
Ambiguous failure

Level 4
Long-horizon debugging

Level 5
Multiple interacting failures

Level 6
Partial observability

Level 7
Multi-agent coordination
```

Difficulty must be measured empirically.

Do not label a task "expert" merely because it looks difficult to a human.

---

# 52. Task Generation

Automated task generation is a future feature.

Generated tasks must pass:

```text
syntactic validation
environment validation
reference solution validation
evaluator validation
baseline agent testing
difficulty calibration
leakage inspection
human review
```

Generated tasks must never automatically enter the official benchmark.

---

# 53. Prohibited Architectural Choices

Unless explicitly approved as a later research requirement, do NOT add:

```text
LangChain
LangGraph
AutoGen
CrewAI
cloud inference APIs
OpenAI API
Anthropic API
Google API
PostgreSQL
Redis
Kubernetes
Kafka
RabbitMQ
hosted vector databases
hosted observability
hosted experiment tracking
```

This is not a statement that these technologies are bad.

The reason is architectural discipline and the project's zero-budget/local-first constraint.

If a later experiment genuinely requires one, document the reason before adding it.

---

# 54. Prohibited Code Patterns

Do NOT:

```text
hard-code API keys
```

Do NOT:

```text
execute agent-generated shell commands on the host
```

Do NOT:

```text
import task-specific evaluator logic into generic agent code
```

Do NOT:

```text
hard-code one model into Agent
```

Do NOT:

```text
hard-code one task into Environment
```

Do NOT:

```text
hard-code reward values inside agent implementations
```

Do NOT:

```text
store hidden ground truth in publicly accessible task files
```

Do NOT:

```text
modify evaluator behavior based on the agent's output
```

Do NOT:

```text
silently change experiment configuration
```

---

# 55. Dependency Rules

Every dependency must answer:

1. Why is it necessary?
2. Why can't the functionality be implemented simply in the project?
3. Does it create a paid or cloud dependency?
4. Does it complicate reproducibility?
5. Does it couple the project to a particular vendor?

Prefer the standard library when the functionality is trivial.

Prefer small, focused libraries over large agent frameworks.

---

# 56. Code Quality

All production Python code should:

- use type hints;
- use Pydantic for external/data schemas;
- use clear names;
- avoid global mutable state;
- use explicit dependency injection;
- have tests for important behavior;
- avoid hidden side effects.

Formatting and linting should be automated once the basic project is stable.

---

# 57. Logging

Use structured logging where possible.

Logs should contain:

```text
timestamp
episode_id
agent_id
event_type
message
metadata
```

Do not log secrets.

Do not log evaluator ground truth into agent-visible logs.

---

# 58. Error Handling

Agent failure is an expected research outcome.

Do not hide failures.

A failed tool call should produce a structured event:

```text
tool_call
exit_code
stdout
stderr
error_type
```

The system should distinguish:

```text
agent failure
tool failure
environment failure
evaluator failure
infrastructure failure
```

These are scientifically different.

---

# 59. Determinism

Where possible:

- seed environments;
- seed pseudo-random generators;
- record seeds;
- pin dependencies;
- pin container images;
- record model configuration.

LLM inference may remain nondeterministic depending on model/runtime configuration.

That nondeterminism must be recorded rather than ignored.

---

# 60. Model Usage Measurement

Every model interaction should record available usage information.

At minimum:

```text
model
input token count
output token count
generation duration
model load duration
```

Ollama's API exposes several of these metrics directly.

These metrics are important because the project explicitly studies performance under resource constraints.

---

# 61. Local Data Storage

Initial storage should be:

```text
SQLite
+
JSONL
+
Parquet
```

Do not introduce a database server.

SQLite stores:

```text
tasks
experiments
episodes
metadata
aggregate metrics
```

JSONL stores:

```text
raw trajectories
```

Parquet stores:

```text
large analytical datasets
```

DuckDB may later be added for analysis over Parquet.

---

# 62. Experiment Directory

Recommended:

```text
results/
└── exp_000001/
    ├── config.json
    ├── environment.json
    ├── model.json
    ├── episodes/
    │   ├── episode_000001.jsonl
    │   └── episode_000002.jsonl
    ├── metrics.json
    └── evaluation.json
```

Do not mix results from different experiments.

---

# 63. Development Order

Implementation MUST proceed in this order unless there is a documented reason to deviate.

## Phase 1

Project skeleton.

## Phase 2

Core types and protocols.

## Phase 3

Ollama provider.

## Phase 4

Tool system.

## Phase 5

Docker environment.

## Phase 6

Single-agent loop.

## Phase 7

Trajectory recording.

## Phase 8

Evaluator.

## Phase 9

ECDSA task integration.

## Phase 10

Multi-agent communication.

## Phase 11

Static orchestration.

## Phase 12

Critic/verifier.

## Phase 13

Research metrics.

## Phase 14

RL orchestrator.

## Phase 15

Additional environments.

---

# 64. Definition of Done for Phase 1

Phase 1 is complete when:

```text
python environment works
project imports successfully
tests execute
CLI starts
configuration loads
```

---

# 65. Definition of Done for Single-Agent MVP

The MVP is complete when:

```text
Ollama
    ↓
Agent
    ↓
Terminal Tool
    ↓
Docker
    ↓
Task
    ↓
Evaluator
    ↓
Trajectory
```

works end-to-end.

A command equivalent to:

```text
arena run --task ecdsa_nonce_bias_001
```

must produce a reproducible episode artifact.

---

# 66. Definition of Done for Multi-Agent MVP

The multi-agent MVP is complete when:

```text
Explorer
Researcher
Executor
```

can:

- receive role-specific context;
- communicate;
- execute tools;
- share selected memory;
- produce a complete trajectory;
- receive a final evaluation.

---

# 67. Definition of Done for RL MVP

The first RL milestone is complete when:

```text
environment state
    ↓
orchestrator policy
    ↓
agent selection
    ↓
episode
    ↓
reward
    ↓
policy update
```

can run locally.

The RL policy must be reproducible from a saved configuration/checkpoint.

---

# 68. Research Integrity

The project must distinguish:

```text
observation
hypothesis
result
interpretation
claim
```

Do not encode a desired research conclusion into the evaluator.

If multi-agent systems perform worse than single agents, report that result.

If RL fails to improve orchestration, report that result.

The purpose of the platform is measurement, not confirmation of the project's hypothesis.

---

# 69. Benchmark Integrity

A benchmark task must have:

```text
clear objective
isolated environment
trusted evaluator
reference solution
known difficulty
reproducible setup
```

The evaluator must test the actual objective.

A benchmark must not reward agents for exploiting accidental implementation details.

---

# 70. Security Principle

Treat every agent as untrusted code execution.

Even though the models are local, their generated commands may be destructive.

The system must assume:

```text
agent may make mistakes
agent may execute destructive commands
agent may attempt to escape the environment
agent may discover unintended files
agent may attempt evaluator manipulation
```

Isolation is therefore mandatory.

---

# 71. Future Model Backend

The architecture must permit:

```text
Ollama
```

as the initial backend while allowing future providers.

Potential future backends:

```text
vLLM
local transformers
other OpenAI-compatible servers
```

No agent implementation should directly depend on the Ollama API.

---

# 72. Future RL Backend

The first RL implementation may be simple.

Future infrastructure may support:

```text
PyTorch
Stable-Baselines3
RLlib
custom policy implementations
```

RL libraries should remain adapters around the Agent Arena environment rather than defining the project's entire architecture.

---

# 73. Future Distributed Execution

Distributed execution is explicitly out of scope for the initial implementation.

The architecture may eventually support:

```text
Ray
RLlib
parallel Docker environments
```

but local execution must remain fully functional.

---

# 74. Future Benchmark

The eventual benchmark should contain environments from multiple domains:

```text
cryptography
security
Linux
networking
DevOps
databases
distributed systems
software engineering
forensics
```

The first benchmark should prioritize quality over quantity.

Five excellent tasks are more valuable than fifty poorly validated tasks.

---

# 75. First Research Experiments

The first experiments should be:

## Experiment A

Single 14B generalist.

## Experiment B

Three-agent team:

```text
8B Explorer
14B Researcher
8B Executor
```

## Experiment C

Three 8B agents.

## Experiment D

Static orchestration versus adaptive orchestration.

## Experiment E

Communication enabled versus communication budgeted.

These experiments should be run under controlled resource budgets.

---

# 76. Central Research Metric

The project should eventually study:

\[
Performance =
f(
task\ success,
compute\ cost,
time,
communication,
recovery,
safety
)
\]

The objective is not simply:

\[
maximize\ success
\]

but approximately:

\[
maximize
\frac{useful\ task\ performance}
{computational\ and\ operational\ cost}
\]

---

# 77. Golden Rule

When implementing a new feature, ask:

> Does this improve the ability to measure, understand, train, or evaluate autonomous terminal-agent behavior?

If the answer is no, the feature probably does not belong in the core platform.

---

# 78. Final Architectural Principle

The most important rule in this repository is:

```text
Do not optimize the architecture for today's model.
Optimize the architecture for tomorrow's experiment.
```

Ollama is today's inference runtime.

The agent abstraction is the research interface.

Docker is today's environment isolation mechanism.

Gymnasium/PettingZoo are the RL interfaces.

The evaluator is the source of truth.

The trajectory is the primary research artifact.

The orchestrator is the eventual learning target.

The benchmark is the experimental substrate.

The research question is the product.

---

# 79. Immediate Implementation Target

Do not implement the entire repository at once.

The first implementation should create only:

```text
AGENTS.md
README.md
LICENSE
pyproject.toml

arena/
    __init__.py
    core/
    models/
    agents/
    tools/
    environments/
    trajectories/

tests/
```

Then implement:

```text
OllamaProvider
TerminalTool
DockerEnvironment
SingleAgent
TrajectoryRecorder
```

Then connect them.

Only after that should the ECDSA environment be integrated.

Do not implement:

```text
RL
PettingZoo
Critic
Verifier
Learned Orchestrator
Task Generator
Distributed Execution
```

until the single-agent vertical slice works.

---

# 80. First Vertical Slice

The first successful execution should look like:

```text
Task
 ↓
Create Docker container
 ↓
Agent receives objective
 ↓
Agent inspects environment
 ↓
Agent calls terminal tool
 ↓
Terminal executes inside container
 ↓
Result returned to agent
 ↓
Agent continues
 ↓
Evaluator checks final state
 ↓
Reward calculated
 ↓
Trajectory saved
 ↓
Container destroyed
```

Command:

```text
arena run --task ecdsa_nonce_bias_001
```

Expected output:

```text
Task: ecdsa_nonce_bias_001
Agent: explorer/executor
Model: <local Ollama model>

Status: SUCCESS / FAILURE

Reward: <value>
Steps: <value>
Tool calls: <value>
Duration: <value>

Trajectory:
results/<episode>.jsonl
```

This is the first real milestone.

Everything else comes after this.
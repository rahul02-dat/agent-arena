# AGENTS.md

# Agent Arena — Runtime and ECDSA MVP Repair Specification

## 0. Mission

You are modifying the existing `rahul02-dat/cryptography` repository.

Your objective is to make the current Agent Arena implementation function correctly **end-to-end** for the ECDSA biased-nonce benchmark while preserving the research architecture defined by this project.

The current implementation reaches evaluation but produces an empty:

```text
/app/private_key.txt
```

The evaluator therefore fails all three tests before cryptographic correctness can even be evaluated.

This is primarily an **agent/runtime execution failure**, not yet a cryptographic correctness failure.

Do not weaken the evaluator to make the benchmark pass.

Fix the runtime, agent loop, task integration, artifact handling, and infrastructure first.

---

# 1. Authoritative Project Principles

The following concepts MUST remain separate:

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

Do not collapse them into one abstraction.

The architecture must permit:

```text
Model A + Agent Role X
Model A + Agent Role Y
Model B + Agent Role X
Model B + Agent Role Y
```

without changing the task environment or evaluator.

The architecture must eventually support:

```text
Single agent
Multi-agent
Static orchestration
LLM orchestration
RL orchestration
```

without rewriting task environments.

The evaluator is the source of truth.

The trajectory is a primary research artifact.

Docker is the isolation boundary.

Ollama is the initial inference backend, but agent code must not depend directly on the Ollama API.

These principles are part of the original project specification.

---

# 2. Current Priority

Do NOT implement the entire future Agent Arena roadmap.

The immediate priority is:

```text
Task
 ↓
Configuration
 ↓
Docker environment
 ↓
Agent receives objective
 ↓
Agent observes environment
 ↓
Agent calls terminal tool
 ↓
Terminal executes inside Docker
 ↓
Structured tool result returns to agent
 ↓
Agent continues reasoning
 ↓
Agent creates required artifact
 ↓
Runtime validates artifact
 ↓
Evaluator validates final state
 ↓
Reward/score
 ↓
Trajectory saved
 ↓
Container destroyed
```

This is the required single-agent vertical slice.

Do not move to RL, learned orchestration, distributed execution, or other future infrastructure until this path is reliable.

---

# 3. Required Success Condition

The command equivalent to:

```bash
arena run --task ecdsa_nonce_bias_001
```

must produce a complete reproducible episode.

A successful run must:

1. Create the Docker environment.
2. Load the task configuration.
3. Configure the model from configuration.
4. Give the agent the legitimate task objective.
5. Give the agent access to the terminal tool.
6. Execute terminal commands inside Docker.
7. Return structured tool results to the agent.
8. Allow the agent to continue for sufficient steps.
9. Require the agent to create:
   `/app/private_key.txt`
10. Validate the artifact before submission.
11. Run the protected evaluator.
12. Return structured evaluation.
13. Record the complete trajectory.
14. Destroy the container.

Expected CLI output:

```text
Task: ecdsa_nonce_bias_001
Agent: executor
Model: <configured model>

Status: SUCCESS / FAILURE

Reward: <value>
Steps: <value>
Tool calls: <value>
Duration: <value>

Trajectory:
results/<episode>.jsonl
```

---

# 4. Critical Bug #1 — Remove Hard-Coded Model Selection

## Current problem

The current CLI hard-codes:

```python
model_name="llama3.2"
```

This is unacceptable for the research architecture.

The model must be configurable.

## Required implementation

The task/experiment configuration must specify:

```yaml
model:
  name: <model-name>
  temperature: 0.0
```

The runtime must read the configured value.

Do NOT write:

```python
OllamaProvider(model_name="llama3.2")
```

inside the execution path.

Instead:

```python
model_config = config["model"]

provider = OllamaProvider(
    model_name=model_config["name"],
    temperature=model_config.get("temperature", 0.0),
)
```

The exact API may differ according to the existing implementation, but the dependency direction must remain:

```text
configuration
    ↓
LLMProvider
    ↓
Ollama implementation
```

The agent must not directly instantiate Ollama internals.

The original specification explicitly requires a generic `LLMProvider` abstraction so that Ollama can later be replaced by other backends.

---

# 5. Critical Bug #2 — Fix Structured Tool-Calling

## Current problem

The current runtime converts tool calls into ordinary text such as:

```text
assistant:
Called tool terminal with arguments ...

user:
Tool result from terminal:
...
```

This is not a proper structured multi-turn tool-calling conversation.

The agent must retain the original assistant tool-call message and receive a structured tool result.

The project specification explicitly expects structured tool calling and multi-turn agent loops.

## Required conversation model

The runtime must preserve:

```text
assistant
    tool_calls:
        terminal(...)
            ↓
terminal tool
            ↓
tool
    tool_call_id = same ID
    content = result
            ↓
assistant
```

Do NOT flatten tool calls into fake assistant/user messages.

## Required data preservation

For every tool call preserve, where available:

```text
tool_call_id
tool name
arguments
assistant message
tool result
stdout
stderr
exit code
error type
```

The tool result must be associated with the exact tool call that produced it.

---

# 6. Critical Bug #3 — Agent Must Not Be Able to Submit an Empty Artifact

The current runtime accepts:

```text
submit
```

without verifying that the requested output exists.

This must be fixed.

Before accepting a submission, execute an environment-side validation.

For this task:

```text
/app/private_key.txt
```

must:

1. Exist.
2. Be a regular file.
3. Be non-empty.
4. Contain a valid hexadecimal integer.
5. Represent a scalar satisfying:

```text
0 < d < N
```

where:

```text
N =
0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
```

The runtime may perform only format/range validation.

It MUST NOT access:

```text
/tests/ground_truth.json
```

or otherwise leak the answer.

If artifact validation fails, do not terminate the episode as successful.

Return a structured failure to the agent, for example:

```text
Submission rejected:
required artifact /app/private_key.txt is missing or invalid.
Continue working.
```

This creates a proper recovery loop.

---

# 7. Critical Bug #4 — Do Not Change the Evaluator to Accommodate the Agent

The evaluator is correct to reject:

```text
/app/private_key.txt = ""
```

The current evaluator reads the file and parses it as hexadecimal.

The evaluator then checks:

```text
0 < d < N
```

and exact equality with the protected ground truth.

It also independently checks:

```text
d * G == expected_public_key
```

Do NOT:

* change expected output;
* weaken equality;
* expose ground truth;
* accept approximate keys;
* modify the tests to make the current agent pass;
* make the evaluator derive the answer from agent output;
* give the agent access to protected evaluator data.

The benchmark must remain trustworthy.

The original specification requires a clear objective, isolated environment, trusted evaluator, reference solution, known difficulty, and reproducible setup.

---

# 8. Critical Bug #5 — Replace Reward Side-Channel Logic

The current evaluator executes:

```text
/tests/test.sh
```

and then reads:

```text
/logs/verifier/reward.txt
```

This is fragile.

The evaluator should directly consume the test execution result.

Required conceptual API:

```python
evaluation = evaluator.evaluate(...)
```

returning:

```python
{
    "success": bool,
    "score": float,
    "metrics": {...},
    "failure_reason": str | None,
}
```

The evaluator must remain independent of agent reasoning.

The original project specification explicitly defines the evaluator as producing success, score, metrics, and failure reason.

The `test.sh` wrapper may remain temporarily for compatibility, but the platform evaluator must not fundamentally depend on a mutable text file for reward computation.

---

# 9. Critical Bug #6 — Increase and Configure Execution Budget

The current CLI has a hard-coded/default:

```text
max_steps = 100
```

This is not appropriate for an expert cryptanalytic task.

The task involves:

```text
dataset inspection
cryptographic reasoning
HNP formulation
lattice construction
code implementation
debugging
LLL/BKZ
candidate extraction
verification
```

The execution budget must come from task/experiment configuration.

Example:

```yaml
limits:
  max_steps: 500
  timeout_seconds: 1200
```

Do not silently override task configuration with a CLI default.

CLI arguments may override configuration only when explicitly provided.

The task's original intended architecture uses controlled resource budgets and reproducible experiments.

---

# 10. Critical Bug #7 — Actually Enforce Docker Resource Limits

Task configuration must correspond to actual infrastructure.

If configuration says:

```yaml
environment:
  network: disabled

limits:
  cpus: 2
  memory_mb: 2048
  storage_mb: 10240
```

then Docker must actually enforce those constraints.

At minimum enforce:

```text
CPU
memory
network isolation
execution timeout
```

Do not merely place resource limits in prompts or YAML.

The project specification explicitly states that agents must be treated as untrusted code execution and that isolation is mandatory.

---

# 11. Network Configuration Must Be Consistent

The current Docker implementation disables networking:

```text
network_mode="none"
```

That is appropriate for this benchmark.

The task configuration must therefore also state:

```yaml
network: disabled
```

Do not have configuration claim internet access while Docker silently disables it.

Configuration and infrastructure must describe the same experiment.

---

# 12. Task Configuration Must Use One Serialization Format

The repository currently has a file named:

```text
task.yaml
```

but parses it as TOML.

This must be corrected.

Use actual YAML for `task.yaml`.

Example:

```yaml
id: ecdsa_nonce_bias_001
version: "1.0"

name: ECDSA Nonce Bias Recovery

category: cryptography
difficulty: expert

objective:
  type: state_change
  description: >
    Recover the ECDSA private key from the provided biased-nonce
    signature dataset and write it to /app/private_key.txt
    as a hexadecimal integer.

environment:
  runtime: docker
  network: disabled

limits:
  max_steps: 500
  timeout_seconds: 1200
  cpus: 2
  memory_mb: 2048
  storage_mb: 10240

agents:
  max_agents: 1
  communication: false

evaluation:
  correctness: true
```

If the repository intentionally wants TOML instead, rename the file to:

```text
task.toml
```

Do not keep a misleading `.yaml` extension.

---

# 13. Do Not Leak the Solution Explanation

The ECDSA task may contain internal/reference material describing:

```text
HNP
Kannan embedding
LLL
BKZ
```

and other solution methodology.

Do NOT automatically inject hidden/reference solution material into the benchmark agent context.

The benchmark should preserve the intended challenge difficulty.

Separate:

```text
public task instructions
```

from:

```text
reference solution
protected ground truth
```

The original task specification explicitly states that the ECDSA challenge should preserve its difficulty and should not be simplified merely to make the first agent succeed.

For debugging, a separate non-benchmark "methodology-assisted" mode may be implemented later.

---

# 14. Initial Agent Architecture

For the immediate repair, make the single-agent architecture robust first.

Use:

```text
SingleAgent
    ↓
LLMProvider
    ↓
ToolRegistry
    ↓
TerminalTool
    ↓
DockerEnvironment
```

Do NOT prematurely require the multi-agent architecture to solve this immediate runtime bug.

The original specification defines the Single-Agent MVP as the first milestone.

After the vertical slice works, the architecture should support:

```text
Explorer
Researcher
Executor
```

as a later multi-agent MVP.

---

# 15. Agent Prompt Requirements

The agent must receive enough legitimate information to understand:

```text
what task it is solving
where the data is
what output is required
how to submit
```

For this task, the context should clearly communicate:

```text
Dataset:
  /app/data/signatures.json

Required output:
  /app/private_key.txt

Output format:
  hexadecimal integer

Success condition:
  recover the correct private key
```

Do NOT include:

```text
private_key_hex
ground_truth.json
protected evaluator contents
reference solution
```

unless running an explicitly separate debugging mode that is not considered a benchmark episode.

---

# 16. Terminal Tool Requirements

The terminal tool MUST execute commands inside the Docker environment.

It MUST NOT execute agent-generated commands directly on the host.

Required conceptual interface:

```python
terminal.execute(
    command: str,
    timeout: int | None = None,
)
```

Return structured data:

```python
{
    "exit_code": int,
    "stdout": str,
    "stderr": str,
    "duration": float,
}
```

Where applicable include:

```text
error_type
timeout
```

The project specification explicitly requires the terminal tool to execute inside the task environment and not directly on the host.

---

# 17. Environment Failure Classification

The system must distinguish:

```text
agent failure
tool failure
environment failure
evaluator failure
infrastructure failure
```

Do not collapse every failure into:

```text
agent failed
```

For example:

```text
terminal timeout
```

is a tool/environment event.

```text
Docker failed to start
```

is infrastructure failure.

```text
private_key.txt missing
```

is an agent/task-completion failure.

```text
pytest crashed
```

may be evaluator/infrastructure failure depending on cause.

This distinction is required for meaningful research metrics.

---

# 18. Trajectory Recording

The trajectory must record the full episode.

At minimum record:

```text
episode_id
timestamp
step
agent_id
agent_role
observation
action
model response
tool call
tool result
environment event
reward
evaluation
```

Tool calls must include:

```text
tool_call_id
tool_name
arguments
```

Tool results must include:

```text
tool_call_id
stdout
stderr
exit_code
duration
error_type
```

Model interactions should record available:

```text
model
input token count
output token count
generation duration
model load duration
```

The original specification requires fine-grained trajectory recording and model usage measurement.

Trajectory recording must be observational and must not modify agent behavior.

---

# 19. Trajectory Format

Use JSONL.

Recommended:

```text
results/
└── <experiment_id>/
    └── episodes/
        └── episode_<id>.jsonl
```

Each line represents one structured event.

Do not write one giant opaque JSON object containing the entire episode.

Define versioned schemas.

For example:

```json
{
  "schema_version": "1.0",
  "episode_id": "...",
  "step": 12,
  "event_type": "tool_result",
  "agent_id": "executor",
  "tool_call_id": "...",
  "tool_name": "terminal",
  "data": {
    "exit_code": 0,
    "stdout": "...",
    "stderr": ""
  }
}
```

Schema changes require explicit versioning.

---

# 20. Artifact Validation Must Remain Separate from Protected Evaluation

There are two different checks:

## Runtime artifact validation

Allowed:

```text
file exists
file non-empty
valid hex
integer range
```

Not allowed:

```text
compare against ground truth
read protected evaluator data
derive answer from evaluator
```

## Protected evaluation

Allowed:

```text
compare exact private key
derive public key
calculate benchmark score
```

The protected evaluator must remain inaccessible to the agent.

This separation is mandatory for benchmark integrity.

---

# 21. ECDSA Task Requirements

The task must continue using the provided:

```text
/app/data/signatures.json
```

dataset.

Do not replace the benchmark with a trivial private-key lookup.

Do not:

```text
embed the private key in the dataset
copy the ground truth into /app
generate the key at runtime from evaluator data
```

The purpose of the task is to require:

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

as defined by the original task specification.

---

# 22. Cryptographic Task Difficulty

Do not alter the challenge merely to increase the probability of success.

The intended task involves biased ECDSA nonces and recovery of the private key.

The intended solution class may involve:

```text
Hidden Number Problem
lattice construction
Kannan embedding
LLL/BKZ
candidate extraction
public-key verification
```

The runtime should make the task executable correctly.

It should NOT secretly solve the task for the model.

---

# 23. Model Capability Experiments

After runtime correctness is established, support controlled model experiments.

At minimum make it possible to compare:

```text
Model A
Model B
```

under identical:

```text
task
dataset
Docker image
resource limits
step limits
temperature
evaluation
```

The only intended experimental variable should be the model/configuration being studied.

This is necessary for research reproducibility.

---

# 24. Do Not Hard-Code Experimental Conditions

Avoid code such as:

```python
max_steps = 100
model = "llama3.2"
temperature = 0.7
network = False
```

inside the runtime.

Experimental conditions belong in configuration.

The experiment must record:

```text
task
model
agent configuration
orchestration strategy
reward configuration
random seed
resource limits
```

The original project specification explicitly requires reproducible experiment configuration.

---

# 25. Testing Requirements

Before considering the repair complete, implement or update tests for:

## Unit tests

```text
test_config_loading
test_model_configuration
test_tool_call_serialization
test_tool_result_serialization
test_artifact_validation
test_trajectory_schema
test_evaluator_result
```

## Integration tests

```text
test_docker_environment
test_terminal_tool_inside_container
test_agent_tool_loop
test_submission_validation
test_evaluator_integration
test_complete_episode
```

## ECDSA evaluator tests

The existing protected evaluator must continue to pass only when:

```text
/app/private_key.txt
```

contains the correct key.

---

# 26. Mandatory Regression Test

Create a regression test for the exact current failure.

Given:

```text
/app/private_key.txt
```

does not exist or is empty,

the runtime must NOT report:

```text
SUCCESS
```

and must NOT silently finish the episode.

Instead it must report something equivalent to:

```text
Artifact validation failed:
private_key.txt is missing or empty.
```

The agent must be allowed to continue when the configured episode budget permits.

---

# 27. Successful End-to-End Test

Create an integration test using a deterministic/mock agent that writes a known valid fixture key into:

```text
/app/private_key.txt
```

Then verify:

```text
artifact validation succeeds
        ↓
evaluator runs
        ↓
evaluation result is structured
        ↓
trajectory is written
        ↓
container is destroyed
```

This proves that the runtime works independently of LLM intelligence.

This distinction is essential.

First prove:

```text
runtime correctness
```

Then measure:

```text
agent capability
```

Do not conflate them.

---

# 28. Required Debugging Order

When the benchmark fails, diagnose in this order:

### Layer 1 — Infrastructure

Check:

```text
Docker image builds
container starts
container remains alive
network configuration
resource limits
command execution
```

### Layer 2 — Task

Check:

```text
/app/data/signatures.json exists
task configuration loads
objective is passed to agent
required output path is correct
```

### Layer 3 — Tool

Check:

```text
tool call parsed
arguments parsed
command executed
stdout returned
stderr returned
exit code returned
```

### Layer 4 — Agent loop

Check:

```text
assistant message preserved
tool call preserved
tool result returned correctly
agent receives result
agent continues
```

### Layer 5 — Artifact

Check:

```text
private_key.txt exists
private_key.txt non-empty
valid hex
valid range
```

### Layer 6 — Evaluator

Check:

```text
tests copied
tests execute
ground truth remains protected
score calculated
```

### Layer 7 — Cryptanalysis

Only after Layers 1–6 pass should you conclude:

```text
the model failed to solve the cryptographic task
```

This distinction is mandatory.

---

# 29. Required CLI Failure Reporting

Do not only output:

```text
success=false
```

The CLI must identify the failure category.

Example:

```text
Status: FAILURE

Failure category: AGENT_TASK_FAILURE
Reason: Required artifact /app/private_key.txt was not produced.

Steps: 87
Tool calls: 41
Duration: 624.2s

Trajectory:
results/exp_000001/episodes/episode_000001.jsonl
```

Possible categories:

```text
AGENT_FAILURE
TOOL_FAILURE
ENVIRONMENT_FAILURE
EVALUATOR_FAILURE
INFRASTRUCTURE_FAILURE
```

---

# 30. Resource Accounting

Every episode should record:

```text
steps
tool_calls
wall_time
model
input_tokens
output_tokens
```

when available.

These metrics are necessary because the project's research objective is not merely:

```text
maximize task success
```

but to understand task performance under computational and operational costs.

---

# 31. Security Requirements

Treat the agent as untrusted.

The agent may:

```text
make destructive commands
attempt to escape Docker
attempt evaluator manipulation
discover unintended files
consume excessive resources
```

Therefore:

```text
Docker isolation is mandatory.
```

The host filesystem must never become an implicit agent-accessible environment.

The evaluator must remain outside the agent's trust boundary.

Protected data must never be mounted into `/app`.

---

# 32. Do Not Implement Yet

Do NOT implement the following as part of this repair:

```text
RL
PettingZoo
learned orchestrator
distributed execution
Ray
RLlib
task generation
cloud inference
database server
vector database
LangChain
LangGraph
critic/verifier architecture
```

unless required to fix an existing interface.

The project specification explicitly requires the initial implementation to establish the single-agent vertical slice before moving to RL, learned orchestration, or distributed infrastructure.

---

# 33. Future Multi-Agent Architecture

After the single-agent MVP is verified, support:

```text
Explorer
Researcher
Executor
```

with:

```text
role-specific context
communication
selected shared memory
tool execution
complete trajectory
final evaluation
```

The project specification defines this as the Multi-Agent MVP.

Do not make the ECDSA task depend on multi-agent execution until the single-agent path is already stable.

---

# 34. Definition of Done — Runtime Repair

The runtime repair is complete only when all of the following are true:

```text
[ ] Model is configurable.
[ ] Agent does not directly depend on Ollama.
[ ] Task objective reaches the agent.
[ ] Task instructions reach the agent.
[ ] Docker environment starts correctly.
[ ] Docker network policy matches configuration.
[ ] Docker resource limits are actually enforced.
[ ] Terminal executes only inside Docker.
[ ] Structured tool calls are preserved.
[ ] Structured tool results return to the agent.
[ ] Tool call IDs are preserved.
[ ] Agent can continue after tool execution.
[ ] max_steps is configurable.
[ ] timeout is configurable.
[ ] Artifact validation occurs before submit.
[ ] Empty private_key.txt cannot be submitted.
[ ] Invalid hexadecimal output cannot be submitted.
[ ] Protected ground truth is not exposed.
[ ] Evaluator independently validates correctness.
[ ] Evaluator returns structured results.
[ ] Reward is not dependent on fragile side-channel state.
[ ] Failure categories are distinguishable.
[ ] Complete trajectory is recorded.
[ ] Model/tool/resource metadata is recorded.
[ ] Container is destroyed after the episode.
```

---

# 35. Definition of Done — ECDSA Benchmark

The ECDSA benchmark integration is complete when:

```text
[ ] /app/data/signatures.json is available.
[ ] Agent receives the legitimate task objective.
[ ] Agent can inspect the dataset.
[ ] Agent can create code inside the container.
[ ] Agent can execute cryptanalytic experiments.
[ ] Agent can write /app/private_key.txt.
[ ] Runtime validates the artifact.
[ ] Protected evaluator validates exact correctness.
[ ] Public-key rederivation test passes.
[ ] Evaluation result is recorded.
[ ] Trajectory is recorded.
[ ] Container is cleaned up.
```

A failed cryptanalytic attempt after all of the above works should be classified as:

```text
AGENT_TASK_FAILURE
```

not:

```text
INFRASTRUCTURE_FAILURE
```

---

# 36. Required Implementation Strategy

Do not rewrite the repository blindly.

Follow this sequence:

## Step 1

Inspect the current repository.

Identify:

```text
CLI
agent
model provider
terminal tool
Docker environment
task configuration
evaluator
trajectory recorder
```

## Step 2

Write tests that reproduce the current failure.

Specifically verify:

```text
empty /app/private_key.txt
```

cannot be submitted successfully.

## Step 3

Fix structured tool calling.

## Step 4

Fix model configuration.

## Step 5

Fix artifact validation.

## Step 6

Fix evaluator result handling.

## Step 7

Fix Docker resource enforcement.

## Step 8

Fix configuration format/consistency.

## Step 9

Fix trajectory recording.

## Step 10

Run a deterministic mock-agent integration test.

## Step 11

Run the actual ECDSA benchmark.

## Step 12

Only then diagnose cryptanalytic/model performance.

---

# 37. Acceptance Criteria

Do not declare the task complete merely because:

```text
pytest starts
```

Do not declare it complete merely because:

```text
Docker starts
```

Do not declare it complete merely because:

```text
the agent makes tool calls
```

The minimum acceptance criterion is:

```text
agent → tool → Docker → artifact → evaluator → reward → trajectory
```

working end-to-end.

The original project defines the Single-Agent MVP in essentially these terms.

---

# 38. Final Rule

Do not optimize the architecture around the current model.

Optimize the architecture around future experiments.

The project specification's central architectural principle is:

```text
Do not optimize the architecture for today's model.
Optimize the architecture for tomorrow's experiment.
```

Ollama is the current inference runtime.

The agent abstraction is the research interface.

Docker is the current isolation mechanism.

The evaluator is the source of truth.

The trajectory is a primary research artifact.

The orchestrator is a future learning target.

The benchmark is the experimental substrate.

The research question is the product.

---

# 39. Final Instruction to the Coding Agent

Implement the changes above directly in the repository.

Do not merely describe the changes.

For every modification:

1. Inspect the existing implementation.
2. Preserve compatible interfaces where practical.
3. Modify only what is necessary.
4. Add regression tests.
5. Run the relevant tests.
6. Run the complete vertical-slice integration test.
7. Run the ECDSA evaluator.
8. Report the exact remaining failure if the cryptanalytic agent still cannot recover the key.

Do not hide failures.

Do not weaken the evaluator.

Do not expose ground truth.

Do not claim success until the complete pipeline has been demonstrated.
import json
import tempfile
from pathlib import Path

from arena.trajectories.recorder import TrajectoryRecorder
from arena.trajectories.schema import ExperimentManifest, TrajectoryEvent


def test_trajectory_event_schema():
    event = TrajectoryEvent(
        schema_version="1.0",
        episode_id="ep_001",
        step=1,
        event_type="tool_result",
        agent_id="Agent-1",
        agent_role="EXECUTOR",
        data={"exit_code": 0, "stdout": "hello", "stderr": ""},
    )
    serialized = json.loads(event.model_dump_json())
    assert serialized["schema_version"] == "1.0"
    assert serialized["episode_id"] == "ep_001"
    assert serialized["data"]["stdout"] == "hello"


def test_manifest_serialization():
    manifest = ExperimentManifest(
        experiment_id="exp_test",
        task_id="ecdsa_nonce_bias_001",
        task_version="1.0",
        model_name="llama3.2",
        model_params={"temperature": 0.0},
        agent_config={"identity": "Agent-1", "role": "EXECUTOR"},
        orchestration_config={"type": "sequential"},
        limits={"max_steps": 500},
        environment_config={"network": "disabled"},
    )
    serialized = json.loads(manifest.model_dump_json(by_alias=True))
    assert serialized["schema_version"] == "1.0"
    assert serialized["experiment_id"] == "exp_test"
    assert serialized["model_config"]["temperature"] == 0.0


def test_trajectory_recorder_collision_safe_and_manifest():
    with tempfile.TemporaryDirectory() as tmpdir:
        rec1 = TrajectoryRecorder(output_dir=tmpdir)
        rec2 = TrajectoryRecorder(output_dir=tmpdir)

        # Collision-safe IDs check
        assert rec1.experiment_id != rec2.experiment_id
        assert rec1.episode_id != rec2.episode_id

        # Write manifest
        manifest_data = {
            "task_id": "ecdsa_nonce_bias_001",
            "task_version": "1.0",
            "model_name": "llama3.2",
            "model_config": {"temperature": 0.0},
        }
        rec1.write_manifest(manifest_data)

        manifest_file = Path(tmpdir) / rec1.experiment_id / "manifest.json"
        assert manifest_file.exists()
        with open(manifest_file, "r", encoding="utf-8") as f:
            saved_manifest = json.load(f)
        assert saved_manifest["task_id"] == "ecdsa_nonce_bias_001"
        assert saved_manifest["model_config"]["temperature"] == 0.0

        # Record step
        event = rec1.record_step(
            {
                "type": "observation",
                "content": "initial observation",
            },
            step=0,
            agent_id="Agent-1",
        )
        assert event.schema_version == "1.0"
        assert event.step == 0
        assert event.event_type == "observation"

        # Check JSONL file
        assert rec1.file_path.exists()
        with open(rec1.file_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert len(lines) == 1
        assert lines[0]["schema_version"] == "1.0"
        assert lines[0]["data"]["content"] == "initial observation"

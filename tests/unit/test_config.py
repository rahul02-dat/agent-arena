from pathlib import Path
import yaml

from arena.core.types import AgentRole
from arena.agents.roles import ROLES
from arena.cli.main import resolve_task_dir


def test_agent_roles_exist():
    assert AgentRole.EXPLORER in ROLES
    assert AgentRole.EXECUTOR in ROLES


def test_task_yaml_loading():
    task_dir = resolve_task_dir("ecdsa_nonce_bias_001")
    assert task_dir.is_dir()

    task_yaml_path = task_dir / "task.yaml"
    assert task_yaml_path.exists()

    with open(task_yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["id"] == "ecdsa_nonce_bias_001"
    assert config["version"] == "1.0"
    assert "model" in config
    assert "environment" in config
    assert config["environment"]["network"] == "disabled"
    assert "limits" in config
    assert config["limits"]["timeout_seconds"] == 1200
    assert config["limits"]["max_steps"] == 500


def test_task_dir_resolution():
    dir_by_id = resolve_task_dir("ecdsa_nonce_bias_001")
    assert dir_by_id.name == "ecdsa_nonce_bias_001"

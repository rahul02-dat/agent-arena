import pytest
from pathlib import Path

from arena.environments.docker import DockerEnvironment
from arena.tools.terminal import TerminalTool


@pytest.fixture(scope="module")
def docker_env():
    task_dir = Path("tasks") / "ecdsa_nonce_bias_001"
    env = DockerEnvironment(
        task_dir=str(task_dir),
        cpus=1,
        memory_mb=512,
        network="disabled",
        default_cmd_timeout=5,
    )
    env.create()
    yield env
    env.destroy()


def test_docker_container_alive_and_network_disabled(docker_env):
    # Basic command execution
    res = docker_env.execute("echo 'arena_test'")
    assert res["exit_code"] == 0
    assert "arena_test" in res["stdout"]

    # Network isolation verification: curl or ping outside must fail
    net_res = docker_env.execute("ping -c 1 -W 1 1.1.1.1")
    assert net_res["exit_code"] != 0


def test_docker_command_timeout(docker_env):
    # sleep 5 with timeout 1s should time out cleanly
    res = docker_env.execute("sleep 5", timeout=1)
    assert res["exit_code"] == -1
    assert res.get("error_type") == "timeout"
    assert "timed out" in res["stderr"].lower()


def test_docker_output_truncation(docker_env):
    # Generate 10KB with max_output_bytes = 1000
    res = docker_env.execute("python3 -c \"print('A' * 10000)\"", max_output_bytes=1000)
    assert res["exit_code"] == 0
    assert res.get("truncated") is True
    assert "byte limit exceeded" in res["stdout"]


def test_terminal_tool_inside_docker(docker_env):
    tool = TerminalTool(environment=docker_env)
    res = tool.execute(command="pwd")
    assert res["exit_code"] == 0
    assert "/app" in res["stdout"]

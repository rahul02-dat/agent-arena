import docker
import tarfile
import io
import os
import time
from pathlib import Path
from typing import Any, Dict

from arena.environments.base import BaseEnvironment


class DockerEnvironment(BaseEnvironment):
    def __init__(
        self,
        task_dir: str,
        image_tag: str = "agent-arena-task",
        cpus: int | None = None,
        memory_mb: int | None = None,
        network: str | None = None,
    ):
        self.client = docker.from_env()
        self.task_dir = Path(task_dir)
        self.image_tag = image_tag
        self.cpus = cpus
        self.memory_mb = memory_mb
        self.network = network
        self.container = None

    def create(self, force_rebuild: bool = False) -> None:
        env_path = self.task_dir / "environment"

        if not env_path.exists():
            raise Exception(
                f"Environment directory not found: {env_path}"
            )

        build_needed = force_rebuild
        if not build_needed:
            try:
                self.client.images.get(self.image_tag)
            except docker.errors.ImageNotFound:
                build_needed = True

        if build_needed:
            self.client.images.build(
                path=str(env_path),
                tag=self.image_tag,
                rm=True,
                forcerm=True,
            )

        run_kwargs = {
            "command": ["tail", "-f", "/dev/null"],
            "detach": True,
            "working_dir": "/app",
        }

        if self.network == "disabled":
            run_kwargs["network_mode"] = "none"

        if self.cpus is not None:
            run_kwargs["nano_cpus"] = int(self.cpus * 1e9)

        if self.memory_mb is not None:
            run_kwargs["mem_limit"] = f"{self.memory_mb}m"

        self.container = self.client.containers.run(
            self.image_tag,
            **run_kwargs
        )

    def reset(self) -> Any:
        self.destroy()
        self.create()
        return self.observe()

    def observe(self) -> Any:
        res = self.execute("pwd")

        if res.get("exit_code", -1) != 0:
            return "Failed to get observation."

        pwd = res.get("output", "").strip()

        ls_res = self.execute("ls -la")

        return (
            f"CWD: {pwd}\n"
            f"{ls_res.get('output', '')}"
        )

    def execute(
        self,
        action: str,
    ) -> Dict[str, Any]:
        if not self.container:
            return {
                "error": "Container not running",
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "output": "",
                "duration": 0.0,
            }

        start_time = time.time()
        exec_res = self.container.exec_run(
            ["/bin/sh", "-lc", action],
            workdir="/app",
            demux=True,
        )
        duration = time.time() - start_time
        
        stdout_bytes, stderr_bytes = exec_res.output
        
        stdout_str = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        stderr_str = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

        return {
            "exit_code": exec_res.exit_code,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "output": stdout_str + stderr_str,
            "duration": duration,
        }

    def copy_to_container(
        self,
        src_path: str,
        dest_path: str,
    ) -> bool:
        if not self.container:
            return False

        src = Path(src_path)

        if not src.exists():
            return False

        tar_stream = io.BytesIO()

        with tarfile.open(
            fileobj=tar_stream,
            mode="w",
        ) as tar:
            tar.add(
                src,
                arcname=os.path.basename(src),
            )

        tar_stream.seek(0)

        return self.container.put_archive(
            path=dest_path,
            data=tar_stream,
        )

    def snapshot(self) -> None:
        pass

    def destroy(self) -> None:
        if self.container:
            try:
                self.container.stop(timeout=1)
                self.container.remove(force=True)
            except Exception:
                pass

            self.container = None

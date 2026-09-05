import concurrent.futures
import docker
import io
import os
import tarfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from arena.environments.base import BaseEnvironment


class DockerEnvironment(BaseEnvironment):
    ALLOWED_NETWORKS = {"disabled", "isolated", "allowed"}

    def __init__(
        self,
        task_dir: str,
        image_tag: str = "agent-arena-task",
        cpus: int | None = None,
        memory_mb: int | None = None,
        storage_mb: int | None = None,
        network: str | None = None,
        default_cmd_timeout: int = 60,
        max_output_bytes: int = 100 * 1024,
    ):
        self.client = docker.from_env()
        self.task_dir = Path(task_dir)
        self.image_tag = image_tag
        self.cpus = cpus
        self.memory_mb = memory_mb
        self.storage_mb = storage_mb
        self.default_cmd_timeout = default_cmd_timeout
        self.max_output_bytes = max_output_bytes

        if network is not None and network not in self.ALLOWED_NETWORKS:
            raise ValueError(
                f"Invalid network mode: '{network}'. "
                f"Must be one of {sorted(list(self.ALLOWED_NETWORKS))}."
            )
        self.network = network

        self.container = None
        self.reset_count = 0
        self.metadata: Dict[str, Any] = {}

    def create(self, force_rebuild: bool = False) -> None:
        env_path = self.task_dir / "environment"

        if not env_path.exists():
            raise FileNotFoundError(
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

        run_kwargs: Dict[str, Any] = {
            "command": ["tail", "-f", "/dev/null"],
            "detach": True,
            "working_dir": "/app",
        }

        if self.network in ("disabled", "isolated"):
            run_kwargs["network_mode"] = "none"
        elif self.network == "allowed":
            run_kwargs["network_mode"] = "bridge"

        if self.cpus is not None:
            run_kwargs["nano_cpus"] = int(self.cpus * 1e9)

        if self.memory_mb is not None:
            run_kwargs["mem_limit"] = f"{self.memory_mb}m"

        if self.storage_mb is not None:
            run_kwargs["storage_opt"] = {"size": f"{self.storage_mb}M"}

        try:
            self.container = self.client.containers.run(
                self.image_tag,
                **run_kwargs,
            )
        except docker.errors.APIError as exc:
            # Fall back if host daemon does not support storage_opt
            if "storage_opt" in run_kwargs:
                run_kwargs.pop("storage_opt")
                self.container = self.client.containers.run(
                    self.image_tag,
                    **run_kwargs,
                )
            else:
                raise exc

        image_id = self.container.image.id if self.container.image else ""
        self.metadata = {
            "container_id": self.container.id,
            "image_id": image_id,
            "image_tag": self.image_tag,
            "cpus": self.cpus,
            "memory_mb": self.memory_mb,
            "storage_mb": self.storage_mb,
            "network": self.network,
            "reset_count": self.reset_count,
            "created_at": time.time(),
        }

    def reset(self) -> Any:
        self.reset_count += 1
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
        timeout: Optional[int] = None,
        max_output_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self.container:
            return {
                "error": "Container not running",
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "output": "",
                "duration": 0.0,
                "error_type": "container_not_running",
            }

        cmd_timeout = timeout if timeout is not None else self.default_cmd_timeout
        max_bytes = max_output_bytes if max_output_bytes is not None else self.max_output_bytes

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self.container.exec_run,
                ["/bin/sh", "-lc", action],
                workdir="/app",
                demux=True,
            )
            try:
                exec_res = future.result(timeout=cmd_timeout)
            except concurrent.futures.TimeoutError:
                duration = time.time() - start_time
                timeout_msg = f"Command timed out after {cmd_timeout} seconds."
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": timeout_msg,
                    "output": timeout_msg,
                    "duration": duration,
                    "error_type": "timeout",
                }

        duration = time.time() - start_time

        stdout_bytes, stderr_bytes = exec_res.output
        stdout_bytes = stdout_bytes or b""
        stderr_bytes = stderr_bytes or b""

        truncated = False
        if len(stdout_bytes) > max_bytes:
            stdout_bytes = stdout_bytes[:max_bytes] + b"\n... [stdout truncated: byte limit exceeded]"
            truncated = True

        if len(stderr_bytes) > max_bytes:
            stderr_bytes = stderr_bytes[:max_bytes] + b"\n... [stderr truncated: byte limit exceeded]"
            truncated = True

        stdout_str = stdout_bytes.decode("utf-8", errors="replace")
        stderr_str = stderr_bytes.decode("utf-8", errors="replace")

        result: Dict[str, Any] = {
            "exit_code": exec_res.exit_code,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "output": stdout_str + stderr_str,
            "duration": duration,
        }
        if truncated:
            result["truncated"] = True

        return result

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

    def snapshot(self) -> Optional[str]:
        if not self.container:
            return None
        try:
            snapshot_tag = f"{self.image_tag}-snapshot"
            self.container.commit(repository=snapshot_tag)
            return snapshot_tag
        except Exception:
            return None

    def destroy(self) -> None:
        if self.container:
            try:
                self.container.stop(timeout=1)
                self.container.remove(force=True)
            except Exception:
                pass

            self.container = None

import docker
import tarfile
import io
import os
from pathlib import Path
from typing import Any, Dict

from arena.environments.base import BaseEnvironment


class DockerEnvironment(BaseEnvironment):
    def __init__(
        self,
        task_dir: str,
        image_tag: str = "agent-arena-task",
    ):
        self.client = docker.from_env()
        self.task_dir = Path(task_dir)
        self.image_tag = image_tag
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

        self.container = self.client.containers.run(
            self.image_tag,
            command=["tail", "-f", "/dev/null"],
            detach=True,
            network_mode="none",
            working_dir="/app",
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
                "output": "",
            }

        exec_res = self.container.exec_run(
            ["/bin/sh", "-lc", action],
            workdir="/app",
        )

        return {
            "exit_code": exec_res.exit_code,
            "output": exec_res.output.decode(
                "utf-8",
                errors="replace",
            ),
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

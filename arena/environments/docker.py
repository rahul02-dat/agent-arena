from typing import Any
from arena.environments.base import BaseEnvironment

class DockerEnvironment(BaseEnvironment):
    def create(self) -> None:
        print("[DockerEnvironment] Created container.")

    def reset(self) -> Any:
        print("[DockerEnvironment] Reset container.")
        return "Initial observation."

    def observe(self) -> Any:
        return "Directory contents: file1.txt, secret.key"

    def execute(self, action: Any) -> Any:
        print(f"[DockerEnvironment] Executed action: {action}")
        return "Command executed successfully."

    def snapshot(self) -> None:
        print("[DockerEnvironment] Snapshot taken.")

    def destroy(self) -> None:
        print("[DockerEnvironment] Container destroyed.")

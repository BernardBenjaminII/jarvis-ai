from dataclasses import dataclass
from pathlib import Path
import platform

from core.src.discovery.runtime_locator import RuntimeLocator


@dataclass(frozen=True)
class RuntimePaths:
    runtime: Path
    project: Path
    knowledge: Path
    memory: Path
    models: Path
    logs: Path
    venvs: Path
    temp: Path


def get_runtime_paths() -> RuntimePaths:
    env = "windows" if platform.system() == "Windows" else "unix"

    runtime = RuntimeLocator(env).locate()

    if runtime is None:
        raise RuntimeError("Unable to locate JARVIS runtime.")

    project = Path(__file__).resolve().parents[3]

    return RuntimePaths(
        runtime=runtime,
        project=project,
        knowledge=runtime / "knowledge",
        memory=runtime / "memory",
        models=runtime / "ollama" / "models",
        logs=runtime / "logs",
        venvs=runtime / "venvs",
        temp=runtime / "temp",
    )

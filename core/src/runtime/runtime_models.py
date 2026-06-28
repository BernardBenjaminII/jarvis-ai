from dataclasses import dataclass
from pathlib import Path


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


@dataclass(frozen=True)
class SystemInfo:
    os_name: str
    environment: str
    hostname: str
    python: Path


@dataclass(frozen=True)
class RuntimeContext:
    paths: RuntimePaths
    system: SystemInfo

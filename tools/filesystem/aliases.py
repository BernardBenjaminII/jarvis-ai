from pathlib import Path

from core.src.discovery.runtime_context import get_runtime_paths

paths = get_runtime_paths()

ALIASES = {
    "runtime": paths.runtime,
    "project": paths.project,
    "knowledge": paths.knowledge,
    "memory": paths.memory,
    "models": paths.models,
    "logs": paths.logs,
    "venvs": paths.venvs,
    "temp": paths.temp,
}


def resolve_path(value: str | Path) -> Path:
    raw = str(value).strip()

    if raw.startswith("@"):
        raw = raw[1:]

    return ALIASES.get(raw.lower(), Path(raw).expanduser())

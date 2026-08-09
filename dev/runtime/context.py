from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    project_root: Path
    python_executable: Path
    python_version: str
    working_directory: Path
    platform: str
    repository_verified: bool
    genesis_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "python_executable": str(self.python_executable),
            "python_version": self.python_version,
            "working_directory": str(self.working_directory),
            "platform": self.platform,
            "repository_verified": self.repository_verified,
            "genesis_version": self.genesis_version,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )

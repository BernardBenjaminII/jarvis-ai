"""Immutable Mission Compiler contracts.

These contracts describe the output of deterministic mission compilation.
They do not execute missions, grant authorization, or mutate source plans.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.executive.models import Mission as RuntimeMission


@dataclass(frozen=True, slots=True)
class CompilationMapping:
    """Trace one planning command into one runtime mission task."""

    planning_mission_id: str
    objective_id: str
    planning_task_id: str
    activity_id: str
    command_id: str
    runtime_mission_id: str
    runtime_task_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "planning_mission_id": self.planning_mission_id,
            "objective_id": self.objective_id,
            "planning_task_id": self.planning_task_id,
            "activity_id": self.activity_id,
            "command_id": self.command_id,
            "runtime_mission_id": self.runtime_mission_id,
            "runtime_task_id": self.runtime_task_id,
        }


@dataclass(frozen=True, slots=True)
class CompilationManifest:
    """Deterministic evidence describing one compilation operation."""

    compiler_version: str
    source_plan_id: str
    source_plan_version: int
    source_plan_fingerprint: str
    planning_mission_id: str
    runtime_mission_id: str
    mappings: tuple[CompilationMapping, ...]
    warnings: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "compiler_version": self.compiler_version,
            "source_plan_id": self.source_plan_id,
            "source_plan_version": self.source_plan_version,
            "source_plan_fingerprint": self.source_plan_fingerprint,
            "planning_mission_id": self.planning_mission_id,
            "runtime_mission_id": self.runtime_mission_id,
            "mappings": [
                mapping.to_dict()
                for mapping in self.mappings
            ],
            "warnings": list(self.warnings),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class MissionCompilationResult:
    """Compiled runtime mission and its immutable evidence manifest."""

    runtime_mission: RuntimeMission
    manifest: CompilationManifest
    task_sources: Mapping[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime_mission": self.runtime_mission.to_dict(),
            "manifest": self.manifest.to_dict(),
            "task_sources": dict(self.task_sources),
        }

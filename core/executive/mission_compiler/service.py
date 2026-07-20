"""Deterministic lowering of planning missions into runtime missions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from core.executive.mission_compiler.contracts import (
    CompilationManifest,
    CompilationMapping,
    MissionCompilationResult,
)
from core.executive.mission_compiler.errors import (
    CyclicRuntimeDependencyError,
    DuplicatePlanElementError,
    EmptyMissionPlanError,
    UnknownDependencyElementError,
    UnsupportedDependencyError,
)
from core.executive.models import (
    Mission as RuntimeMission,
    MissionStatus as RuntimeMissionStatus,
    MissionTask as RuntimeMissionTask,
)
from core.executive.planning.models import (
    Command as PlanningCommand,
    Mission as PlanningMission,
    PlanVersion,
)


COMPILER_VERSION = "9c2a.1"


@dataclass(frozen=True, slots=True)
class _CommandContext:
    """One command together with its complete planning ancestry."""

    mission: PlanningMission
    objective_id: str
    objective_name: str
    planning_task_id: str
    planning_task_name: str
    responsible_capability: str | None
    activity_id: str
    activity_name: str
    command: PlanningCommand


class MissionCompiler:
    """Compile immutable planning data into the existing runtime model.

    The compiler is deliberately conservative:

    - one planning Command becomes one runtime MissionTask;
    - command identifiers are preserved as runtime task identifiers;
    - only command-to-command dependencies are lowered in IX-C2A;
    - authorization requirements are preserved as data but are not granted;
    - no task is executed during compilation;
    - source PlanVersion objects are never mutated.
    """

    compiler_version = COMPILER_VERSION

    def compile(
        self,
        plan_version: PlanVersion,
    ) -> MissionCompilationResult:
        """Compile a planning PlanVersion into a runtime Mission."""

        contexts = self._collect_commands(
            plan_version.mission
        )

        if not contexts:
            raise EmptyMissionPlanError(
                "Planning mission contains no executable commands"
            )

        self._validate_unique_elements(
            plan_version.mission,
            contexts,
        )

        command_ids = {
            context.command.command_id
            for context in contexts
        }

        dependencies = self._lower_dependencies(
            plan_version=plan_version,
            command_ids=command_ids,
        )

        self._assert_acyclic(
            command_ids=command_ids,
            dependencies=dependencies,
        )

        runtime_mission_id = self._runtime_mission_id(
            plan_version
        )

        runtime_tasks = [
            self._compile_command(
                context=context,
                runtime_mission_id=runtime_mission_id,
                depends_on=dependencies.get(
                    context.command.command_id,
                    (),
                ),
                plan_version=plan_version,
            )
            for context in contexts
        ]

        runtime_mission = RuntimeMission(
            mission_id=runtime_mission_id,
            objective=(
                plan_version.mission.commander_intent
            ),
            context=self._mission_context(plan_version),
            status=RuntimeMissionStatus.PLANNED,
            tasks=runtime_tasks,
        )

        mappings = tuple(
            CompilationMapping(
                planning_mission_id=(
                    context.mission.mission_id
                ),
                objective_id=context.objective_id,
                planning_task_id=(
                    context.planning_task_id
                ),
                activity_id=context.activity_id,
                command_id=context.command.command_id,
                runtime_mission_id=runtime_mission_id,
                runtime_task_id=context.command.command_id,
            )
            for context in contexts
        )

        warnings = self._collect_warnings(
            plan_version
        )

        fingerprint = self._manifest_fingerprint(
            plan_version=plan_version,
            runtime_mission=runtime_mission,
            mappings=mappings,
            warnings=warnings,
        )

        manifest = CompilationManifest(
            compiler_version=self.compiler_version,
            source_plan_id=plan_version.plan_id,
            source_plan_version=plan_version.version,
            source_plan_fingerprint=(
                plan_version.fingerprint
            ),
            planning_mission_id=(
                plan_version.mission.mission_id
            ),
            runtime_mission_id=runtime_mission_id,
            mappings=mappings,
            warnings=warnings,
            fingerprint=fingerprint,
        )

        task_sources = {
            mapping.runtime_task_id: mapping.command_id
            for mapping in mappings
        }

        return MissionCompilationResult(
            runtime_mission=runtime_mission,
            manifest=manifest,
            task_sources=task_sources,
        )

    def _collect_commands(
        self,
        mission: PlanningMission,
    ) -> tuple[_CommandContext, ...]:
        contexts: list[_CommandContext] = []

        for objective in mission.objectives:
            for task in objective.tasks:
                for activity in task.activities:
                    for command in activity.commands:
                        contexts.append(
                            _CommandContext(
                                mission=mission,
                                objective_id=(
                                    objective.objective_id
                                ),
                                objective_name=objective.name,
                                planning_task_id=task.task_id,
                                planning_task_name=task.name,
                                responsible_capability=(
                                    task.responsible_capability
                                ),
                                activity_id=(
                                    activity.activity_id
                                ),
                                activity_name=activity.name,
                                command=command,
                            )
                        )

        return tuple(contexts)

    def _validate_unique_elements(
        self,
        mission: PlanningMission,
        contexts: tuple[_CommandContext, ...],
    ) -> None:
        identifiers: list[str] = [
            mission.mission_id,
        ]

        for objective in mission.objectives:
            identifiers.append(objective.objective_id)

            for task in objective.tasks:
                identifiers.append(task.task_id)

                for activity in task.activities:
                    identifiers.append(
                        activity.activity_id
                    )

        identifiers.extend(
            context.command.command_id
            for context in contexts
        )

        duplicate_ids = sorted(
            identifier
            for identifier in set(identifiers)
            if identifiers.count(identifier) > 1
        )

        if duplicate_ids:
            raise DuplicatePlanElementError(
                "Duplicate planning element identifiers: "
                + ", ".join(duplicate_ids)
            )

    def _lower_dependencies(
        self,
        plan_version: PlanVersion,
        command_ids: set[str],
    ) -> dict[str, tuple[str, ...]]:
        all_element_ids = self._all_element_ids(
            plan_version.mission
        )
        lowered: dict[str, list[str]] = {
            command_id: []
            for command_id in command_ids
        }

        for dependency in plan_version.dependencies:
            predecessor = dependency.predecessor_id
            successor = dependency.successor_id

            unknown = [
                identifier
                for identifier in (
                    predecessor,
                    successor,
                )
                if identifier not in all_element_ids
            ]

            if unknown:
                raise UnknownDependencyElementError(
                    "Dependency references unknown plan "
                    "element(s): "
                    + ", ".join(sorted(unknown))
                )

            if (
                predecessor not in command_ids
                or successor not in command_ids
            ):
                raise UnsupportedDependencyError(
                    "IX-C2A can lower only command-to-command "
                    "dependencies. Unsupported dependency: "
                    f"{predecessor} -> {successor}"
                )

            lowered[successor].append(predecessor)

        return {
            successor: tuple(sorted(set(predecessors)))
            for successor, predecessors
            in lowered.items()
        }

    def _all_element_ids(
        self,
        mission: PlanningMission,
    ) -> set[str]:
        identifiers = {
            mission.mission_id,
        }

        for objective in mission.objectives:
            identifiers.add(objective.objective_id)

            for task in objective.tasks:
                identifiers.add(task.task_id)

                for activity in task.activities:
                    identifiers.add(
                        activity.activity_id
                    )

                    for command in activity.commands:
                        identifiers.add(
                            command.command_id
                        )

        return identifiers

    def _compile_command(
        self,
        context: _CommandContext,
        runtime_mission_id: str,
        depends_on: tuple[str, ...],
        plan_version: PlanVersion,
    ) -> RuntimeMissionTask:
        command = context.command

        director = (
            context.responsible_capability
            or command.capability
        )

        payload = {
            "parameters": dict(command.parameters),
            "planning": {
                "plan_id": plan_version.plan_id,
                "plan_version": plan_version.version,
                "plan_fingerprint": (
                    plan_version.fingerprint
                ),
                "planning_mission_id": (
                    context.mission.mission_id
                ),
                "objective_id": context.objective_id,
                "objective_name": (
                    context.objective_name
                ),
                "planning_task_id": (
                    context.planning_task_id
                ),
                "planning_task_name": (
                    context.planning_task_name
                ),
                "activity_id": context.activity_id,
                "activity_name": context.activity_name,
                "command_id": command.command_id,
            },
            "authorization": {
                "mode": command.authorization.mode.value,
                "approving_authority": (
                    command.authorization
                    .approving_authority
                ),
                "inherited_from_parent": (
                    command.authorization
                    .inherited_from_parent
                ),
                "conditions": list(
                    command.authorization.conditions
                ),
                "boundaries": list(
                    command.authorization.boundaries
                ),
                "granted": False,
            },
            "execution_contract": {
                "expected_output": (
                    command.expected_output
                ),
                "timeout_seconds": (
                    command.timeout_seconds
                ),
                "retry_limit": command.retry_limit,
                "reversible": command.reversible,
                "rollback_operation": (
                    command.rollback_operation
                ),
                "completion_criteria": list(
                    command.completion_criteria
                ),
            },
            "metadata": dict(command.metadata),
            "runtime_mission_id": runtime_mission_id,
        }

        return RuntimeMissionTask(
            task_id=command.command_id,
            title=command.name,
            director=director,
            action=command.operation,
            payload=payload,
            depends_on=list(depends_on),
            required_capabilities=[
                command.capability
            ],
            routing_evidence={
                "source": "mission_compiler",
                "compiler_version": (
                    self.compiler_version
                ),
                "planning_command_id": (
                    command.command_id
                ),
                "responsible_capability": (
                    context.responsible_capability
                ),
            },
        )

    def _mission_context(
        self,
        plan_version: PlanVersion,
    ) -> dict[str, Any]:
        mission = plan_version.mission

        return {
            "source": "mission_compiler",
            "compiler_version": self.compiler_version,
            "plan_id": plan_version.plan_id,
            "plan_version": plan_version.version,
            "plan_fingerprint": (
                plan_version.fingerprint
            ),
            "planning_mission_id": mission.mission_id,
            "title": mission.title,
            "commander_intent": (
                mission.commander_intent
            ),
            "desired_end_state": (
                mission.desired_end_state
            ),
            "owner": mission.owner,
            "priority": mission.priority.value,
            "completion_criteria": list(
                mission.completion_criteria
            ),
            "prohibitions": list(
                mission.prohibitions
            ),
            "authorization": {
                "mode": mission.authorization.mode.value,
                "approving_authority": (
                    mission.authorization
                    .approving_authority
                ),
                "granted": False,
            },
            "metadata": dict(mission.metadata),
        }

    def _runtime_mission_id(
        self,
        plan_version: PlanVersion,
    ) -> str:
        return (
            f"runtime_{plan_version.plan_id}"
            f"_v{plan_version.version}"
        )

    def _collect_warnings(
        self,
        plan_version: PlanVersion,
    ) -> tuple[str, ...]:
        warnings: list[str] = []

        mission = plan_version.mission

        if mission.assumptions:
            warnings.append(
                "Planning assumptions remain unresolved at "
                "compilation time."
            )

        if mission.risks:
            warnings.append(
                "Planning risks were preserved as context but "
                "were not converted into runtime controls."
            )

        if mission.resources:
            warnings.append(
                "Mission resource requirements were preserved "
                "as planning data but were not allocated."
            )

        if mission.constraints:
            warnings.append(
                "Mission constraints were preserved but require "
                "runtime enforcement by later phases."
            )

        return tuple(sorted(warnings))

    def _manifest_fingerprint(
        self,
        plan_version: PlanVersion,
        runtime_mission: RuntimeMission,
        mappings: tuple[CompilationMapping, ...],
        warnings: tuple[str, ...],
    ) -> str:
        payload = {
            "compiler_version": self.compiler_version,
            "source_plan_id": plan_version.plan_id,
            "source_plan_version": plan_version.version,
            "source_plan_fingerprint": (
                plan_version.fingerprint
            ),
            "runtime_mission": (
                runtime_mission.to_dict()
            ),
            "mappings": [
                mapping.to_dict()
                for mapping in mappings
            ],
            "warnings": list(warnings),
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    def _assert_acyclic(
        self,
        command_ids: Iterable[str],
        dependencies: Mapping[
            str,
            tuple[str, ...],
        ],
    ) -> None:
        permanent: set[str] = set()
        temporary: set[str] = set()

        def visit(command_id: str) -> None:
            if command_id in permanent:
                return

            if command_id in temporary:
                raise CyclicRuntimeDependencyError(
                    "Compiled runtime dependency graph "
                    f"contains a cycle at {command_id}"
                )

            temporary.add(command_id)

            for predecessor in dependencies.get(
                command_id,
                (),
            ):
                visit(predecessor)

            temporary.remove(command_id)
            permanent.add(command_id)

        for command_id in sorted(command_ids):
            visit(command_id)

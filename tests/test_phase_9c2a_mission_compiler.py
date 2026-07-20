"""Tests for Phase IX-C2A deterministic mission compilation."""

from __future__ import annotations

import unittest

from core.executive.mission_compiler import (
    CyclicRuntimeDependencyError,
    EmptyMissionPlanError,
    MissionCompiler,
    UnsupportedDependencyError,
)
from core.executive.models import (
    MissionStatus as RuntimeMissionStatus,
)
from core.executive.planning.enums import (
    AuthorizationMode,
    PlanState,
)
from core.executive.planning.models import (
    Activity,
    AuthorizationRequirement,
    Command,
    Dependency,
    Mission,
    Objective,
    PlanVersion,
    Task,
)


def authorization() -> AuthorizationRequirement:
    return AuthorizationRequirement(
        mode=AuthorizationMode.COMMANDER_APPROVAL,
        approving_authority="commander",
    )


def build_plan_version(
    *,
    include_dependency: bool = True,
    higher_level_dependency: bool = False,
    cyclic: bool = False,
) -> PlanVersion:
    auth = authorization()

    first_command = Command(
        command_id="command_analyze",
        activity_id="activity_analysis",
        name="Analyze objective",
        description="Analyze the mission objective.",
        capability="analysis",
        operation="analyze",
        authorization=auth,
        parameters={"depth": "full"},
        expected_output="Structured analysis",
        completion_criteria=("Analysis produced",),
    )

    second_command = Command(
        command_id="command_synthesize",
        activity_id="activity_analysis",
        name="Synthesize result",
        description="Synthesize the analyzed evidence.",
        capability="synthesis",
        operation="synthesize",
        authorization=auth,
        expected_output="Mission result",
        completion_criteria=("Result produced",),
    )

    activity = Activity(
        activity_id="activity_analysis",
        task_id="task_primary",
        name="Primary activity",
        description="Perform analysis and synthesis.",
        authorization=auth,
        commands=(
            first_command,
            second_command,
        ),
        completion_criteria=(
            "Commands completed",
        ),
    )

    task = Task(
        task_id="task_primary",
        objective_id="objective_primary",
        name="Primary task",
        description="Complete the primary work.",
        expected_output="Completed objective",
        authorization=auth,
        activities=(activity,),
        completion_criteria=(
            "Primary work complete",
        ),
        responsible_capability="operations",
    )

    objective = Objective(
        objective_id="objective_primary",
        mission_id="mission_planning",
        name="Primary objective",
        description="Achieve the desired result.",
        desired_outcome="Desired result achieved",
        tasks=(task,),
        completion_criteria=(
            "Desired result achieved",
        ),
    )

    mission = Mission(
        mission_id="mission_planning",
        title="Compiler fixture mission",
        commander_intent="Compile and execute the fixture",
        desired_end_state="Fixture execution succeeds",
        owner="commander",
        objectives=(objective,),
        completion_criteria=(
            "All runtime tasks complete",
        ),
        authorization=auth,
    )

    dependencies: tuple[Dependency, ...] = ()

    if include_dependency:
        if higher_level_dependency:
            dependencies = (
                Dependency(
                    dependency_id="dependency_higher",
                    predecessor_id="objective_primary",
                    successor_id="command_synthesize",
                ),
            )
        elif cyclic:
            dependencies = (
                Dependency(
                    dependency_id="dependency_one",
                    predecessor_id="command_analyze",
                    successor_id="command_synthesize",
                ),
                Dependency(
                    dependency_id="dependency_two",
                    predecessor_id="command_synthesize",
                    successor_id="command_analyze",
                ),
            )
        else:
            dependencies = (
                Dependency(
                    dependency_id="dependency_normal",
                    predecessor_id="command_analyze",
                    successor_id="command_synthesize",
                ),
            )

    return PlanVersion(
        plan_id="plan_fixture",
        version=1,
        mission=mission,
        state=next(iter(PlanState)),
        dependencies=dependencies,
    )


class MissionCompilerTests(unittest.TestCase):
    def test_compiles_commands_into_runtime_tasks(self) -> None:
        compiler = MissionCompiler()
        result = compiler.compile(
            build_plan_version()
        )

        runtime = result.runtime_mission

        self.assertEqual(
            runtime.mission_id,
            "runtime_plan_fixture_v1",
        )
        self.assertEqual(
            runtime.status,
            RuntimeMissionStatus.PLANNED,
        )
        self.assertEqual(len(runtime.tasks), 2)

        task_ids = [
            task.task_id
            for task in runtime.tasks
        ]

        self.assertEqual(
            task_ids,
            [
                "command_analyze",
                "command_synthesize",
            ],
        )

        self.assertEqual(
            runtime.tasks[1].depends_on,
            ["command_analyze"],
        )

    def test_preserves_planning_provenance(self) -> None:
        result = MissionCompiler().compile(
            build_plan_version()
        )

        task = result.runtime_mission.tasks[0]
        planning = task.payload["planning"]

        self.assertEqual(
            planning["planning_mission_id"],
            "mission_planning",
        )
        self.assertEqual(
            planning["objective_id"],
            "objective_primary",
        )
        self.assertEqual(
            planning["planning_task_id"],
            "task_primary",
        )
        self.assertEqual(
            planning["activity_id"],
            "activity_analysis",
        )
        self.assertEqual(
            planning["command_id"],
            "command_analyze",
        )

    def test_deterministic_manifest_fingerprint(self) -> None:
        plan = build_plan_version()
        compiler = MissionCompiler()

        first = compiler.compile(plan)
        second = compiler.compile(plan)

        self.assertEqual(
            first.manifest.fingerprint,
            second.manifest.fingerprint,
        )
        self.assertEqual(
            first.runtime_mission.to_dict(),
            second.runtime_mission.to_dict(),
        )

    def test_authorization_is_not_silently_granted(self) -> None:
        result = MissionCompiler().compile(
            build_plan_version()
        )

        for task in result.runtime_mission.tasks:
            authorization_payload = (
                task.payload["authorization"]
            )
            self.assertFalse(
                authorization_payload["granted"]
            )

    def test_rejects_higher_level_dependency(self) -> None:
        plan = build_plan_version(
            higher_level_dependency=True,
        )

        with self.assertRaises(
            UnsupportedDependencyError
        ):
            MissionCompiler().compile(plan)

    def test_rejects_dependency_cycle(self) -> None:
        plan = build_plan_version(
            cyclic=True,
        )

        with self.assertRaises(
            CyclicRuntimeDependencyError
        ):
            MissionCompiler().compile(plan)

    def test_rejects_empty_plan(self) -> None:
        auth = authorization()

        mission = Mission(
            mission_id="mission_empty",
            title="Empty mission",
            commander_intent="Compile nothing",
            desired_end_state="No execution",
            owner="commander",
            completion_criteria=(
                "No work exists",
            ),
            authorization=auth,
        )

        plan = PlanVersion(
            plan_id="plan_empty",
            version=1,
            mission=mission,
            state=next(iter(PlanState)),
        )

        with self.assertRaises(
            EmptyMissionPlanError
        ):
            MissionCompiler().compile(plan)


if __name__ == "__main__":
    unittest.main()

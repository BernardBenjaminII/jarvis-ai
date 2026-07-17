"""
JARVIS GEN 2
Phase IX-C2

Canonical Mission Planning Data Model Tests
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, replace

from core.executive.planning import (
    Activity,
    AuthorizationMode,
    AuthorizationRequirement,
    Command,
    Dependency,
    DependencyCycleError,
    DependencyType,
    InMemoryPlanRepository,
    InvalidPlanTransitionError,
    Mission,
    MissionPriority,
    Objective,
    PlanState,
    PlanningService,
    Task,
    build_dependency_graph,
)


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------


def commander_auth() -> AuthorizationRequirement:
    return AuthorizationRequirement(
        mode=AuthorizationMode.COMMANDER_APPROVAL,
        approving_authority="commander",
    )


def delegated_auth() -> AuthorizationRequirement:
    return AuthorizationRequirement(
        mode=AuthorizationMode.AUTOMATIC_WITHIN_BOUNDS,
        boundaries=("test_fixture",),
    )


def build_fixture_mission() -> Mission:

    command_collect = Command(
        command_id="command_collect",
        activity_id="activity_collect",
        name="Collect Context",
        description="Collect environment information.",
        capability="planning",
        operation="collect_context",
        authorization=delegated_auth(),
        completion_criteria=("collection complete",),
    )

    command_validate = Command(
        command_id="command_validate",
        activity_id="activity_validate",
        name="Validate Context",
        description="Validate collected information.",
        capability="planning",
        operation="validate_context",
        authorization=delegated_auth(),
        completion_criteria=("validation complete",),
    )

    activity_collect = Activity(
        activity_id="activity_collect",
        task_id="task_collect",
        name="Collection",
        description="Acquire mission context.",
        authorization=delegated_auth(),
        commands=(command_collect,),
        completion_criteria=("collection finished",),
    )

    activity_validate = Activity(
        activity_id="activity_validate",
        task_id="task_validate",
        name="Validation",
        description="Validate mission context.",
        authorization=delegated_auth(),
        commands=(command_validate,),
        completion_criteria=("validation finished",),
    )

    task_collect = Task(
        task_id="task_collect",
        objective_id="objective_main",
        name="Collect Context",
        description="Collect planning context.",
        expected_output="Context collected.",
        authorization=commander_auth(),
        activities=(activity_collect,),
        completion_criteria=("context exists",),
        responsible_capability="planning",
    )

    task_validate = Task(
        task_id="task_validate",
        objective_id="objective_main",
        name="Validate Context",
        description="Validate planning context.",
        expected_output="Context validated.",
        authorization=commander_auth(),
        activities=(activity_validate,),
        completion_criteria=("context validated",),
        responsible_capability="planning",
    )

    objective = Objective(
        objective_id="objective_main",
        mission_id="mission_main",
        name="Verify Planning",
        description="Verify planning subsystem.",
        desired_outcome="Planning contracts operate correctly.",
        tasks=(
            task_collect,
            task_validate,
        ),
        completion_criteria=("planning verified",),
        priority=MissionPriority.HIGH,
    )

    mission = Mission(
        mission_id="mission_main",
        title="Phase IX-C2 Verification",
        commander_intent="Verify canonical planning.",
        desired_end_state="Planning layer validated.",
        owner="commander",
        objectives=(objective,),
        completion_criteria=("verification complete",),
        authorization=commander_auth(),
    )

    return mission


def build_dependencies():

    return (

        Dependency(
            dependency_id="dependency_task",
            predecessor_id="task_collect",
            successor_id="task_validate",
            dependency_type=DependencyType.FINISH_TO_START,
        ),

        Dependency(
            dependency_id="dependency_activity",
            predecessor_id="activity_collect",
            successor_id="activity_validate",
            dependency_type=DependencyType.INFORMATION,
        ),
    )


# ---------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------


class PlanningDataModelTests(unittest.TestCase):

    def test_create_plan(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        plan = service.create_plan(
            mission=build_fixture_mission(),
            dependencies=build_dependencies(),
        )

        self.assertEqual(
            plan.current.version,
            1,
        )

        self.assertEqual(
            plan.current.state,
            PlanState.DRAFT,
        )

        self.assertEqual(
            len(plan.current.fingerprint),
            64,
        )

        report = service.validate(plan.plan_id)

        self.assertTrue(report.passed)

    def test_plan_is_immutable(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        plan = service.create_plan(
            mission=build_fixture_mission(),
        )

        with self.assertRaises(FrozenInstanceError):
            plan.current.state = PlanState.ACTIVE

    def test_fingerprint_is_stable(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        plan = service.create_plan(
            mission=build_fixture_mission(),
        )

        reconstructed = replace(
            plan.current,
            fingerprint="",
        )

        self.assertEqual(
            reconstructed.fingerprint,
            plan.current.fingerprint,
        )

    def test_revision_creates_new_version(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        original = service.create_plan(
            mission=build_fixture_mission(),
        )

        revised_mission = replace(
            build_fixture_mission(),
            title="Phase IX-C2 Revised Mission",
        )

        revised = service.revise_plan(
            plan_id=original.plan_id,
            mission=revised_mission,
            reason="Planning refinement",
        )

        self.assertEqual(
            len(revised.versions),
            2,
        )

        self.assertEqual(
            revised.current.version,
            2,
        )

        self.assertEqual(
            revised.current.parent_version,
            1,
        )

        self.assertEqual(
            revised.get_version(1).mission.title,
            "Phase IX-C2 Verification",
        )

        self.assertEqual(
            revised.get_version(2).mission.title,
            "Phase IX-C2 Revised Mission",
        )

    def test_dependency_graph_order(self):

        graph = build_dependency_graph(
            build_fixture_mission(),
            build_dependencies(),
        )

        ordering = graph.topological_order()

        self.assertLess(
            ordering.index("task_collect"),
            ordering.index("task_validate"),
        )

        self.assertLess(
            ordering.index("activity_collect"),
            ordering.index("activity_validate"),
        )

    def test_dependency_cycle_detection(self):

        dependencies = build_dependencies() + (

            Dependency(
                dependency_id="dependency_cycle",
                predecessor_id="task_validate",
                successor_id="task_collect",
            ),

        )

        with self.assertRaises(
            DependencyCycleError,
        ):
            build_dependency_graph(
                build_fixture_mission(),
                dependencies,
            )

    def test_valid_transition(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        original = service.create_plan(
            mission=build_fixture_mission(),
        )

        updated = service.transition(
            plan_id=original.plan_id,
            target_state=PlanState.CONTEXT_GATHERING,
            reason="Begin planning",
        )

        self.assertEqual(
            updated.current.version,
            2,
        )

        self.assertEqual(
            updated.current.state,
            PlanState.CONTEXT_GATHERING,
        )

    def test_invalid_transition(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        original = service.create_plan(
            mission=build_fixture_mission(),
        )

        with self.assertRaises(
            InvalidPlanTransitionError,
        ):
            service.transition(
                plan_id=original.plan_id,
                target_state=PlanState.ACTIVE,
                reason="Illegal transition",
            )

    def test_json_serialization(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        plan = service.create_plan(
            mission=build_fixture_mission(),
            dependencies=build_dependencies(),
        )

        payload = plan.current.to_dict()

        self.assertEqual(
            payload["version"],
            1,
        )

        self.assertEqual(
            payload["state"],
            "draft",
        )

        self.assertEqual(
            payload["mission"]["mission_id"],
            "mission_main",
        )

        self.assertEqual(
            payload["fingerprint"],
            plan.current.fingerprint,
        )


    def test_repository_round_trip(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        created = service.create_plan(
            mission=build_fixture_mission(),
            dependencies=build_dependencies(),
        )

        loaded = repository.get(created.plan_id)

        self.assertEqual(
            created.plan_id,
            loaded.plan_id,
        )

        self.assertEqual(
            created.current.fingerprint,
            loaded.current.fingerprint,
        )

    def test_repository_lists_plans(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        service.create_plan(
            mission=build_fixture_mission(),
        )

        plans = repository.list_plans()

        self.assertEqual(
            len(plans),
            1,
        )

    def test_plan_validation_after_revision(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        plan = service.create_plan(
            mission=build_fixture_mission(),
        )

        revised = service.revise_plan(
            plan_id=plan.plan_id,
            mission=replace(
                build_fixture_mission(),
                commander_intent="Updated commander intent",
            ),
            reason="Mission refinement",
        )

        report = service.validate(
            revised.plan_id,
        )

        self.assertTrue(
            report.passed,
        )

    def test_plan_history_preserved(self):

        repository = InMemoryPlanRepository()
        service = PlanningService(repository)

        plan = service.create_plan(
            mission=build_fixture_mission(),
        )

        service.revise_plan(
            plan_id=plan.plan_id,
            mission=replace(
                build_fixture_mission(),
                title="Revision One",
            ),
            reason="revision",
        )

        service.revise_plan(
            plan_id=plan.plan_id,
            mission=replace(
                build_fixture_mission(),
                title="Revision Two",
            ),
            reason="revision",
        )

        latest = repository.get(
            plan.plan_id,
        )

        self.assertEqual(
            len(latest.versions),
            3,
        )

        self.assertEqual(
            latest.get_version(1).mission.title,
            "Phase IX-C2 Verification",
        )

        self.assertEqual(
            latest.get_version(2).mission.title,
            "Revision One",
        )

        self.assertEqual(
            latest.get_version(3).mission.title,
            "Revision Two",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from core.cognition.mission_compiler import (
    ActivityExecutionMode,
    ActivitySpecification,
    DecisionNotApprovedError,
    ExecutiveMissionCompiler,
    MissionCompilationRequest,
    MissionDependencyCycleError,
    MissionPlanStatus,
    ObjectiveSpecification,
    OrphanPlanNodeError,
    TaskSpecification,
    to_canonical_data,
)


def request(*, approved: bool = True, cycle: bool = False):
    return MissionCompilationRequest(
        decision_id="decision-a7",
        selected_coa_id="coa-primary",
        decision_approved=approved,
        mission_title="Establish verified mission capability",
        mission_intent="Compile the approved decision into controlled work.",
        request_id="request-a8",
        objectives=(
            ObjectiveSpecification(
                key="foundation",
                title="Build foundation",
                description="Create the validated foundation.",
                success_criteria=("Foundation verified",),
            ),
            ObjectiveSpecification(
                key="integration",
                title="Integrate capability",
                description="Integrate the verified foundation.",
                success_criteria=("Integration verified",),
                depends_on=("foundation",),
            ),
        ),
        tasks=(
            TaskSpecification(
                key="prepare",
                objective_key="foundation",
                title="Prepare",
                description="Prepare required artifacts.",
                verification="Artifacts are present.",
            ),
            TaskSpecification(
                key="integrate",
                objective_key="integration",
                title="Integrate",
                description="Perform controlled integration.",
                verification="Integration tests pass.",
                depends_on=("prepare",),
            ),
        ),
        activities=(
            ActivitySpecification(
                key="write",
                task_key="prepare",
                title="Write artifacts",
                instruction="Create the required artifacts.",
                expected_result="Artifacts exist.",
                verification="Check required paths.",
                execution_mode=ActivityExecutionMode.AUTOMATED,
                depends_on=("verify",) if cycle else (),
            ),
            ActivitySpecification(
                key="verify",
                task_key="integrate",
                title="Verify integration",
                instruction="Run the integration verification.",
                expected_result="Verification passes.",
                verification="Exit status is zero.",
                execution_mode=ActivityExecutionMode.AUTOMATED,
                depends_on=("write",),
            ),
        ),
        observation_ids=("observation-1",),
        evidence_ids=("evidence-1",),
        hypothesis_ids=("hypothesis-1",),
        situation_reference="situation-1",
        reasoning_reference="reasoning-1",
    )


class T(unittest.TestCase):
    def setUp(self):
        self.compiler = ExecutiveMissionCompiler()

    def test_compile(self):
        plan = self.compiler.compile(request())
        self.assertEqual(plan.status, MissionPlanStatus.COMPILED)
        self.assertEqual(len(plan.objectives), 2)
        self.assertEqual(len(plan.tasks), 2)
        self.assertEqual(len(plan.activities), 2)

    def test_determinism(self):
        first = self.compiler.compile(request())
        second = self.compiler.compile(request())
        self.assertEqual(first.mission_id, second.mission_id)
        self.assertEqual(
            first.execution_graph.topological_order,
            second.execution_graph.topological_order,
        )

    def test_decision_gate(self):
        with self.assertRaises(DecisionNotApprovedError):
            self.compiler.compile(request(approved=False))

    def test_cycle_detection(self):
        with self.assertRaises(MissionDependencyCycleError):
            self.compiler.compile(request(cycle=True))

    def test_orphan_task(self):
        bad = request()
        bad_task = TaskSpecification(
            key="bad",
            objective_key="missing",
            title="Bad",
            description="Bad",
            verification="Never",
        )
        changed = MissionCompilationRequest(
            decision_id=bad.decision_id,
            selected_coa_id=bad.selected_coa_id,
            decision_approved=True,
            mission_title=bad.mission_title,
            mission_intent=bad.mission_intent,
            objectives=bad.objectives,
            tasks=(bad_task,),
            activities=bad.activities,
        )
        with self.assertRaises(OrphanPlanNodeError):
            self.compiler.compile(changed)

    def test_trace(self):
        plan = self.compiler.compile(request())
        self.assertEqual(plan.trace.decision_id, "decision-a7")
        self.assertIn("evidence-1", plan.trace.evidence_ids)

    def test_immutable(self):
        plan = self.compiler.compile(request())
        with self.assertRaises(FrozenInstanceError):
            plan.title = "changed"  # type: ignore[misc]

    def test_serialization(self):
        data = to_canonical_data(self.compiler.compile(request()))
        self.assertEqual(data["status"], "compiled")
        self.assertEqual(data["priority"], "normal")


if __name__ == "__main__":
    unittest.main()

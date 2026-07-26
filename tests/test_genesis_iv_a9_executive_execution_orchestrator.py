from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from core.cognition.execution_orchestrator import (
    ActivityExecutionSpec,
    CallableExecutor,
    DispatchMode,
    ExecutionResult,
    ExecutionStatus,
    ExecutiveExecutionOrchestrator,
    ExecutorRegistry,
    InvalidExecutionPlanError,
    MissionExecutionRequest,
    MissionExecutionStatus,
    to_canonical_data,
)


def request(*, approval: bool = False, attempts: int = 1):
    return MissionExecutionRequest(
        mission_id="mission-a8",
        decision_id="decision-a7",
        request_id="request-a9",
        activities=(
            ActivityExecutionSpec(
                activity_id="activity-1",
                title="Prepare",
                instruction="Prepare artifacts.",
                expected_result="Artifacts prepared.",
                verification="Artifacts exist.",
                dispatch_mode=DispatchMode.AUTOMATED,
                required_capability="fixture",
                max_attempts=attempts,
                requires_approval=approval,
            ),
            ActivityExecutionSpec(
                activity_id="activity-2",
                title="Verify",
                instruction="Verify artifacts.",
                expected_result="Verification passes.",
                verification="Exit zero.",
                dispatch_mode=DispatchMode.AUTOMATED,
                required_capability="fixture",
                dependency_ids=("activity-1",),
            ),
        ),
        topological_order=("activity-1", "activity-2"),
    )


class T(unittest.TestCase):
    def registry(self, handler):
        registry = ExecutorRegistry()
        registry.register(CallableExecutor("fixture", handler))
        return registry

    def test_create_snapshot(self):
        orchestrator = ExecutiveExecutionOrchestrator(self.registry(
            lambda ctx: ExecutionResult(True, "ok")
        ))
        snapshot = orchestrator.create_snapshot(request())
        self.assertEqual(snapshot.status, MissionExecutionStatus.CREATED)
        self.assertEqual(snapshot.activities[0].status, ExecutionStatus.PENDING)

    def test_execute_success_path(self):
        orchestrator = ExecutiveExecutionOrchestrator(self.registry(
            lambda ctx: ExecutionResult(True, f"{ctx.activity.activity_id} ok")
        ))
        req = request()
        snapshot = orchestrator.create_snapshot(req)
        result = orchestrator.run_ready(req, snapshot)
        self.assertEqual(result.status, MissionExecutionStatus.SUCCEEDED)
        self.assertTrue(all(
            item.status is ExecutionStatus.SUCCEEDED
            for item in result.activities
        ))

    def test_dependency_order(self):
        calls = []
        def handler(ctx):
            calls.append(ctx.activity.activity_id)
            return ExecutionResult(True, "ok")
        orchestrator = ExecutiveExecutionOrchestrator(self.registry(handler))
        req = request()
        result = orchestrator.run_ready(req, orchestrator.create_snapshot(req))
        self.assertEqual(calls, ["activity-1", "activity-2"])
        self.assertEqual(result.status, MissionExecutionStatus.SUCCEEDED)

    def test_approval_gate(self):
        orchestrator = ExecutiveExecutionOrchestrator(self.registry(
            lambda ctx: ExecutionResult(True, "ok")
        ))
        req = request(approval=True)
        result = orchestrator.run_ready(req, orchestrator.create_snapshot(req))
        self.assertEqual(result.status, MissionExecutionStatus.BLOCKED)
        self.assertEqual(result.activities[0].status, ExecutionStatus.BLOCKED)

    def test_retry(self):
        calls = {"count": 0}
        def handler(ctx):
            calls["count"] += 1
            return ExecutionResult(calls["count"] > 1, "attempt")
        orchestrator = ExecutiveExecutionOrchestrator(self.registry(handler))
        req = request(attempts=2)
        first = orchestrator.run_ready(req, orchestrator.create_snapshot(req))
        self.assertEqual(first.activities[0].status, ExecutionStatus.READY)
        second = orchestrator.run_ready(req, first)
        self.assertEqual(second.status, MissionExecutionStatus.SUCCEEDED)

    def test_human_confirmation(self):
        req = MissionExecutionRequest(
            mission_id="mission-human",
            decision_id="decision-human",
            activities=(
                ActivityExecutionSpec(
                    activity_id="human-1",
                    title="Human step",
                    instruction="Perform review.",
                    expected_result="Review complete.",
                    verification="Human confirms.",
                    dispatch_mode=DispatchMode.HUMAN,
                ),
            ),
            topological_order=("human-1",),
        )
        orchestrator = ExecutiveExecutionOrchestrator()
        blocked = orchestrator.run_ready(req, orchestrator.create_snapshot(req))
        done = orchestrator.confirm_human_completion(
            req,
            blocked,
            "human-1",
            succeeded=True,
            summary="Human confirmed.",
        )
        self.assertEqual(done.status, MissionExecutionStatus.SUCCEEDED)

    def test_invalid_order(self):
        bad = MissionExecutionRequest(
            mission_id="mission-bad",
            decision_id="decision-bad",
            activities=request().activities,
            topological_order=("activity-2", "activity-1"),
        )
        with self.assertRaises(InvalidExecutionPlanError):
            ExecutiveExecutionOrchestrator().create_snapshot(bad)

    def test_immutable(self):
        orchestrator = ExecutiveExecutionOrchestrator()
        snapshot = orchestrator.create_snapshot(request())
        with self.assertRaises(FrozenInstanceError):
            snapshot.status = MissionExecutionStatus.RUNNING  # type: ignore[misc]

    def test_serialization(self):
        orchestrator = ExecutiveExecutionOrchestrator()
        data = to_canonical_data(orchestrator.create_snapshot(request()))
        self.assertEqual(data["status"], "created")
        self.assertEqual(data["activities"][0]["status"], "pending")


if __name__ == "__main__":
    unittest.main()

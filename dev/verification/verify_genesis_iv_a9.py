from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = (
    "core/cognition/execution_orchestrator/__init__.py",
    "core/cognition/execution_orchestrator/contracts.py",
    "core/cognition/execution_orchestrator/enums.py",
    "core/cognition/execution_orchestrator/errors.py",
    "core/cognition/execution_orchestrator/executors.py",
    "core/cognition/execution_orchestrator/orchestrator.py",
    "core/cognition/execution_orchestrator/serialization.py",
    "core/cognition/execution_orchestrator/state.py",
    "tests/test_genesis_iv_a9_executive_execution_orchestrator.py",
    "docs/architecture/genesis_iv_a9_executive_execution_orchestrator.md",
    "docs/decisions/ADR-0036-executive-execution-orchestrator-boundary.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(all((ROOT / path).is_file() for path in REQUIRED), "Canonical IV-A9 file set")

    module = importlib.import_module("core.cognition.execution_orchestrator")
    public = (
        "ExecutiveExecutionOrchestrator",
        "ExecutorRegistry",
        "CallableExecutor",
        "MissionExecutionRequest",
        "ActivityExecutionSpec",
        "ExecutionResult",
        "ExecutionStatus",
        "MissionExecutionStatus",
    )
    check(all(hasattr(module, name) for name in public), "Stable public imports")

    registry = module.ExecutorRegistry()
    registry.register(
        module.CallableExecutor(
            "verify",
            lambda context: module.ExecutionResult(
                succeeded=True,
                summary=f"{context.activity.activity_id} verified",
            ),
        )
    )
    request = module.MissionExecutionRequest(
        mission_id="mission-verify",
        decision_id="decision-verify",
        request_id="request-verify",
        activities=(
            module.ActivityExecutionSpec(
                activity_id="activity-verify",
                title="Verify",
                instruction="Run verification.",
                expected_result="Verification passes.",
                verification="Exit zero.",
                dispatch_mode=module.DispatchMode.AUTOMATED,
                required_capability="verify",
            ),
        ),
        topological_order=("activity-verify",),
    )

    orchestrator = module.ExecutiveExecutionOrchestrator(registry)
    first = orchestrator.create_snapshot(request)
    second = orchestrator.create_snapshot(request)
    check(first.execution_id == second.execution_id, "Deterministic execution identity")

    final = orchestrator.run_ready(request, first)
    check(final.status is module.MissionExecutionStatus.SUCCEEDED, "Controlled execution")
    check(
        final.activities[0].status is module.ExecutionStatus.SUCCEEDED,
        "Activity lifecycle completion",
    )
    check(bool(final.observations), "Execution observation emission")
    check(final.constitution_revision == "CONST-0001/1.0", "Constitution binding")

    payload = {
        "execution_id": final.execution_id,
        "mission_id": final.mission_id,
        "decision_id": final.decision_id,
        "activity_statuses": [
            item.status.value for item in final.activities
        ],
        "constitution": final.constitution_revision,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print(f"[PASS] Deterministic IV-A9 fingerprint: {fingerprint}")


if __name__ == "__main__":
    main()

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
    "core/cognition/mission_compiler/__init__.py",
    "core/cognition/mission_compiler/compiler.py",
    "core/cognition/mission_compiler/contracts.py",
    "core/cognition/mission_compiler/enums.py",
    "core/cognition/mission_compiler/errors.py",
    "core/cognition/mission_compiler/graph.py",
    "core/cognition/mission_compiler/serialization.py",
    "tests/test_genesis_iv_a8_executive_mission_compiler.py",
    "docs/architecture/genesis_iv_a8_executive_mission_compiler.md",
    "docs/decisions/ADR-0035-executive-mission-compiler-boundary.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(all((ROOT / path).is_file() for path in REQUIRED), "Canonical IV-A8 file set")

    module = importlib.import_module("core.cognition.mission_compiler")
    public = (
        "ExecutiveMissionCompiler",
        "MissionCompilationRequest",
        "ObjectiveSpecification",
        "TaskSpecification",
        "ActivitySpecification",
        "MissionPlan",
        "MissionDependencyCycleError",
    )
    check(all(hasattr(module, name) for name in public), "Stable public imports")

    request = module.MissionCompilationRequest(
        decision_id="decision-verify",
        selected_coa_id="coa-verify",
        decision_approved=True,
        mission_title="Verification mission",
        mission_intent="Verify deterministic compilation.",
        request_id="verify-a8",
        objectives=(
            module.ObjectiveSpecification(
                key="objective",
                title="Objective",
                description="Complete verification.",
                success_criteria=("Verification passes",),
            ),
        ),
        tasks=(
            module.TaskSpecification(
                key="task",
                objective_key="objective",
                title="Task",
                description="Run verification.",
                verification="Exit zero.",
            ),
        ),
        activities=(
            module.ActivitySpecification(
                key="activity",
                task_key="task",
                title="Activity",
                instruction="Run checks.",
                expected_result="Checks pass.",
                verification="Exit zero.",
            ),
        ),
        evidence_ids=("evidence-verify",),
    )

    compiler = module.ExecutiveMissionCompiler()
    first = compiler.compile(request)
    second = compiler.compile(request)

    check(first.mission_id == second.mission_id, "Deterministic mission identity")
    check(
        first.execution_graph.topological_order
        == second.execution_graph.topological_order,
        "Deterministic execution graph",
    )
    check(first.trace.decision_id == "decision-verify", "Decision trace preservation")
    check(bool(first.activities), "Executable activity projection")
    check(first.constitution_revision == "CONST-0001/1.0", "Constitution binding")

    payload = {
        "mission_id": first.mission_id,
        "order": first.execution_graph.topological_order,
        "decision": first.decision_id,
        "constitution": first.constitution_revision,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print(f"[PASS] Deterministic IV-A8 fingerprint: {fingerprint}")


if __name__ == "__main__":
    main()

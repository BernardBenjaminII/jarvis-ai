from __future__ import annotations

import json
from pathlib import Path

TRACE_DECL = """_LAST_TRACE: ContextVar[dict[str, Any] | None] = ContextVar(
    "jarvis_last_qualification_trace",
    default=None,
)
"""

RESULT_DECL = """_LAST_RESULT: ContextVar[QualificationResult | None] = ContextVar(
    "jarvis_last_qualification_result",
    default=None,
)
"""

TRACE_SET = """    _LAST_TRACE.set(
        {
"""

RESULT_SET = """    _LAST_RESULT.set(result)

    _LAST_TRACE.set(
        {
"""

TRACE_GETTER = """def get_last_qualification_trace() -> dict[str, Any] | None:
    value = _LAST_TRACE.get()
    return None if value is None else dict(value)
"""

RESULT_GETTER = """def get_last_qualification_result() -> QualificationResult | None:
    return _LAST_RESULT.get()


def get_last_qualification_trace() -> dict[str, Any] | None:
    value = _LAST_TRACE.get()
    return None if value is None else dict(value)
"""

ORCH_ANCHOR = """            synthesis_input = knowledge_state.synthesis_input(synthesis_input)
"""

ORCH_INSERT = """            synthesis_input = knowledge_state.synthesis_input(synthesis_input)

            from core.conversation.grounded_answer.integration import (
                augment_synthesis_input,
            )

            synthesis_input = augment_synthesis_input(
                self,
                context,
                synthesis_input,
            )
"""


def repair_qualified_search(root: Path) -> dict:
    target = root / "core/knowledge_catalog/qualified_search.py"
    source = target.read_text(encoding="utf-8")
    changed = False

    if RESULT_DECL not in source:
        if TRACE_DECL not in source:
            raise RuntimeError("Qualification trace declaration not found.")
        source = source.replace(TRACE_DECL, TRACE_DECL + "\n" + RESULT_DECL, 1)
        changed = True

    if "_LAST_RESULT.set(result)" not in source:
        if TRACE_SET not in source:
            raise RuntimeError("Qualification trace assignment not found.")
        source = source.replace(TRACE_SET, RESULT_SET, 1)
        changed = True

    if "def get_last_qualification_result()" not in source:
        if TRACE_GETTER not in source:
            raise RuntimeError("Qualification trace getter not found.")
        source = source.replace(TRACE_GETTER, RESULT_GETTER, 1)
        changed = True

    target.write_text(source, encoding="utf-8")
    return {
        "target": str(target),
        "status": "repaired" if changed else "already_repaired",
        "changed": changed,
    }


def repair_orchestrator(root: Path) -> dict:
    target = root / "core/conversation/orchestrator.py"
    source = target.read_text(encoding="utf-8")

    if ORCH_INSERT in source:
        return {
            "target": str(target),
            "status": "already_integrated",
            "changed": False,
        }

    if ORCH_ANCHOR not in source:
        raise RuntimeError(
            "Audited knowledge-state synthesis anchor not found. "
            "No orchestrator change applied."
        )

    target.write_text(
        source.replace(ORCH_ANCHOR, ORCH_INSERT, 1),
        encoding="utf-8",
    )
    return {
        "target": str(target),
        "status": "integrated",
        "changed": True,
    }


def main() -> int:
    root = Path.cwd().resolve()
    bridge = repair_qualified_search(root)
    orchestrator = repair_orchestrator(root)

    report = {
        "schema_version": "genesis_ix_a4_7_pack2_v1",
        "qualification_bridge": bridge,
        "orchestrator": orchestrator,
        "runtime_path": (
            "QualificationResult -> GroundedAnswerRuntimeService.plan -> "
            "GroundedAnswerPlan -> existing synthesis handler"
        ),
    }

    output = root / "docs/audits/genesis_ix_a4_7_pack2"
    output.mkdir(parents=True, exist_ok=True)
    (output / "orchestrator_integration.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "orchestrator_integration.md").write_text(
        "# Genesis IX-A4.7 Pack 2 — Executive Orchestrator Integration\n\n"
        f"**Qualification bridge:** `{bridge['status']}`\n"
        f"**Orchestrator:** `{orchestrator['status']}`\n\n"
        "```text\n"
        f"{report['runtime_path']}\n"
        "```\n",
        encoding="utf-8",
    )

    print("[PASS] Qualification result bridge:", bridge["status"])
    print("[PASS] Executive orchestrator:", orchestrator["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

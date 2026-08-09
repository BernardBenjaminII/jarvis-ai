from __future__ import annotations

import json
from pathlib import Path


ANCHOR = """            synthesis_input = knowledge_state.synthesis_input(synthesis_input)
"""

INSERTION = """            synthesis_input = knowledge_state.synthesis_input(synthesis_input)

            from core.conversation.grounded_answer.integration import (
                augment_synthesis_input,
            )

            synthesis_input = augment_synthesis_input(
                self,
                context,
                synthesis_input,
            )
"""


def repair(root: Path) -> dict:
    target = root / "core/conversation/orchestrator.py"

    if not target.is_file():
        raise FileNotFoundError(target)

    source = target.read_text(encoding="utf-8")

    if INSERTION in source:
        status = "already_integrated"
        changed = False
    elif ANCHOR in source:
        source = source.replace(
            ANCHOR,
            INSERTION,
            1,
        )
        target.write_text(
            source,
            encoding="utf-8",
        )
        status = "integrated"
        changed = True
    else:
        raise RuntimeError(
            "The audited knowledge-awareness synthesis anchor was not found. "
            "No production file was changed."
        )

    report = {
        "schema_version": "genesis_ix_a4_7_pack2b_v1",
        "target": str(target),
        "status": status,
        "changed": changed,
        "runtime_path": (
            "QualificationResult -> GroundedAnswerRuntimeService.plan -> "
            "GroundedAnswerPlan -> existing synthesis handler"
        ),
        "retrieval_layer_changes": 0,
    }

    output = root / "docs/audits/genesis_ix_a4_7_pack2b"
    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    (output / "orchestrator_integration.json").write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    (output / "orchestrator_integration.md").write_text(
        "# Genesis IX-A4.7 Pack 2B — Executive Orchestrator Integration\n\n"
        f"**Status:** `{status}`\n"
        f"**Changed:** `{changed}`\n"
        f"**Target:** `{target}`\n"
        f"**Retrieval-layer changes:** `0`\n\n"
        "```text\n"
        f"{report['runtime_path']}\n"
        "```\n",
        encoding="utf-8",
    )

    print(
        "[PASS] Executive orchestrator:",
        status,
    )
    return report


def main() -> int:
    repair(
        Path.cwd().resolve()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

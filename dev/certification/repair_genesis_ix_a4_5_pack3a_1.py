from __future__ import annotations

import json
from pathlib import Path


OLD_BLOCK = """    report = EndToEndRetrievalTracer(
        repository_root=Path(bootstrap.repository_root),
        catalog_database=catalog,
    ).certify()
"""

NEW_BLOCK = """    tracer = EndToEndRetrievalTracer(
        repository_root=Path(bootstrap.repository_root),
        catalog_database=catalog,
    )

    if catalog is None:
        raise RuntimeError(
            "Semantic known-query certification requires a catalog database."
        )

    from core.retrieval.certification.semantic_fixture import (
        install_semantic_fixture_override,
    )

    fixture = install_semantic_fixture_override(
        tracer,
        catalog,
    )
    report = tracer.certify()
"""


def repair(root: Path) -> dict:
    target = (
        root
        / "dev/certification/certify_genesis_ix_a4_3.py"
    )

    if not target.is_file():
        raise FileNotFoundError(target)

    source = target.read_text(encoding="utf-8")

    if NEW_BLOCK in source:
        changed = False
        status = "already_repaired"
    elif OLD_BLOCK in source:
        target.write_text(
            source.replace(OLD_BLOCK, NEW_BLOCK, 1),
            encoding="utf-8",
        )
        changed = True
        status = "repaired"
    else:
        raise RuntimeError(
            "The audited EndToEndRetrievalTracer invocation was not found. "
            "No certification file was changed."
        )

    report = {
        "schema_version": "genesis_ix_a4_5_pack3a_1_v1",
        "target": str(target),
        "status": status,
        "changed": changed,
        "repair": (
            "Instantiate tracer -> discover semantic fixture -> "
            "override live known-query selector -> certify"
        ),
    }

    output = root / "docs/audits/genesis_ix_a4_5_pack3a_1"
    output.mkdir(parents=True, exist_ok=True)

    (output / "fixture_repair.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "fixture_repair.md").write_text(
        "# Genesis IX-A4.5 Pack 3A.1 — Known Query Fixture Repair\n\n"
        f"**Status:** `{status}`\n"
        f"**Changed:** `{changed}`\n"
        f"**Target:** `{target}`\n\n"
        "```text\n"
        f"{report['repair']}\n"
        "```\n",
        encoding="utf-8",
    )

    print("[PASS] Known-query certification fixture:", status)
    return report


def main() -> int:
    repair(Path.cwd().resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

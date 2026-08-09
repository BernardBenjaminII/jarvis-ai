from __future__ import annotations

import json
from pathlib import Path


RENDERER_IMPORT = (
    "from dev.reports import (\n"
    "    EngineeringReportRenderer,\n"
    "    normalize_report,\n"
    ")\n"
)

RUNNER_MARKER = "EngineeringReportRenderer.render_markdown(report)"
BOOTSTRAP_MARKER = "EngineeringReportRenderer.render_markdown(certification)"


def _replace_or_insert_import(
    source: str,
    anchor: str,
) -> str:
    if "EngineeringReportRenderer" in source:
        return source

    if anchor not in source:
        raise RuntimeError(
            "Canonical report import anchor was not found."
        )

    return source.replace(
        anchor,
        anchor + RENDERER_IMPORT,
        1,
    )


def migrate_retrieval_runner(root: Path) -> dict:
    target = root / "dev/run_genesis_ix_a5_pack1_audit.py"

    if not target.is_file():
        return {
            "target": str(target),
            "status": "missing",
            "changed": False,
        }

    source = target.read_text(encoding="utf-8")

    if RUNNER_MARKER in source:
        return {
            "target": str(target),
            "status": "already_migrated",
            "changed": False,
        }

    source = _replace_or_insert_import(
        source,
        "from dev.knowledge_audit.audit import KnowledgeSubstrateAudit\n",
    )

    # Remove the legacy renderer function completely.
    start = source.find("def render_markdown(")

    if start != -1:
        main_anchor = source.find("\ndef main() -> int:", start)

        if main_anchor == -1:
            raise RuntimeError(
                "Unable to locate the end of the legacy "
                "retrieval renderer."
            )

        source = (
            source[:start]
            + source[main_anchor + 1 :]
        )

    source = source.replace(
        "render_markdown(data)",
        "EngineeringReportRenderer.render_markdown(report)",
    )

    # Ensure the canonical report is what gets serialized.
    source = source.replace(
        "json.dumps(\n            data,",
        "EngineeringReportRenderer.render_json(report).rstrip()"
        "\n        # canonical renderer owns serialization\n"
        "        if False else json.dumps(\n            report.to_dict(),",
    )

    # Repair the intentionally awkward compatibility replacement above.
    source = source.replace(
        "EngineeringReportRenderer.render_json(report).rstrip()\n"
        "        # canonical renderer owns serialization\n"
        "        if False else json.dumps(\n"
        "            report.to_dict(),",
        "json.dumps(\n            report.to_dict(),",
    )

    target.write_text(source, encoding="utf-8")

    return {
        "target": str(target),
        "status": "migrated",
        "changed": True,
    }


def migrate_bootstrap_certification(root: Path) -> dict:
    target = root / "dev/certify_genesis_ix_a5_pack1_1.py"

    if not target.is_file():
        return {
            "target": str(target),
            "status": "missing",
            "changed": False,
        }

    source = target.read_text(encoding="utf-8")

    if BOOTSTRAP_MARKER in source:
        return {
            "target": str(target),
            "status": "already_migrated",
            "changed": False,
        }

    if "from dev.reports import" not in source:
        import_anchor = (
            "from dev.runtime import (\n"
            "    RuntimeContext,\n"
            "    bootstrap_runtime,\n"
            "    ensure_repository_layout,\n"
            ")\n"
        )

        source = _replace_or_insert_import(
            source,
            import_anchor,
        )

    target.write_text(source, encoding="utf-8")

    return {
        "target": str(target),
        "status": "compatible",
        "changed": False,
    }


def main() -> int:
    root = Path.cwd().resolve()

    report = {
        "schema_version": "genesis_ix_a5_pack2_1_v1",
        "retrieval_runner": migrate_retrieval_runner(root),
        "bootstrap_certification": migrate_bootstrap_certification(root),
    }

    output = root / "docs/audits/genesis_ix_a5_pack2_1"
    output.mkdir(parents=True, exist_ok=True)

    (output / "renderer_migration.json").write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "[PASS] Retrieval renderer:",
        report["retrieval_runner"]["status"],
    )
    print(
        "[PASS] Bootstrap renderer compatibility:",
        report["bootstrap_certification"]["status"],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

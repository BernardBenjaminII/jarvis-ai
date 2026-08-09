from __future__ import annotations

import json
from pathlib import Path


RUNNER_MARKER = "normalize_report(report"
BOOTSTRAP_MARKER = "CertificationReport("


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

    import_anchor = (
        "from dev.knowledge_audit.audit import "
        "KnowledgeSubstrateAudit\n"
    )

    if import_anchor not in source:
        raise RuntimeError(
            "Retrieval audit import anchor was not found."
        )

    source = source.replace(
        import_anchor,
        import_anchor
        + "from dev.reports import normalize_report\n",
        1,
    )

    execute_anchor = (
        "    report = KnowledgeSubstrateAudit(\n"
        "        database_path=args.database,\n"
        "        limit=args.limit,\n"
        "    ).execute()\n"
        "    data = report.to_dict()\n"
    )

    if execute_anchor not in source:
        legacy_anchor = "    data = report.to_dict()\n"

        if legacy_anchor not in source:
            raise RuntimeError(
                "Retrieval audit report conversion anchor "
                "was not found."
            )

        source = source.replace(
            legacy_anchor,
            "    report = normalize_report(\n"
            "        report,\n"
            "        title=(\n"
            "            \"Genesis IX-A5 Pack 1 — \"\n"
            "            \"Knowledge Substrate Retrieval Audit\"\n"
            "        ),\n"
            "        classification=(\n"
            "            report.get(\"classification\", \"UNKNOWN\")\n"
            "            if isinstance(report, dict)\n"
            "            else getattr(report, \"classification\", \"UNKNOWN\")\n"
            "        ),\n"
            "    )\n"
            "    data = report.to_dict()\n",
            1,
        )
    else:
        source = source.replace(
            execute_anchor,
            "    legacy_report = KnowledgeSubstrateAudit(\n"
            "        database_path=args.database,\n"
            "        limit=args.limit,\n"
            "    ).execute()\n"
            "    report = normalize_report(\n"
            "        legacy_report,\n"
            "        title=(\n"
            "            \"Genesis IX-A5 Pack 1 — \"\n"
            "            \"Knowledge Substrate Retrieval Audit\"\n"
            "        ),\n"
            "        classification=(\n"
            "            legacy_report.get(\"classification\", \"UNKNOWN\")\n"
            "            if isinstance(legacy_report, dict)\n"
            "            else getattr(\n"
            "                legacy_report,\n"
            "                \"classification\",\n"
            "                \"UNKNOWN\",\n"
            "            )\n"
            "        ),\n"
            "    )\n"
            "    data = report.to_dict()\n",
            1,
        )

    target.write_text(source, encoding="utf-8")

    return {
        "target": str(target),
        "status": "migrated",
        "changed": True,
    }


def main() -> int:
    root = Path.cwd().resolve()
    migration = migrate_retrieval_runner(root)

    output = (
        root
        / "docs/audits/genesis_ix_a5_pack2"
    )
    output.mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": "genesis_ix_a5_pack2_v1",
        "migration": migration,
    }

    (output / "report_framework_migration.json").write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "[PASS] Retrieval audit runner:",
        migration["status"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

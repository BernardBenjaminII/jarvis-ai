from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from dev.runtime import (
    RuntimeContext,
    bootstrap_runtime,
    ensure_repository_layout,
)
from dev.reports import (
    EngineeringReportRenderer,
    normalize_report,
)


def main() -> int:
    runtime = bootstrap_runtime(Path(__file__))
    root = runtime.project_root
    checks: list[dict[str, object]] = []

    def check(
        code: str,
        passed: bool,
        detail: str,
    ) -> None:
        checks.append(
            {
                "code": code,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    check(
        "ROOT-VALID",
        ensure_repository_layout(root) == root,
        str(root),
    )
    check(
        "CONTEXT-IMMUTABLE",
        RuntimeContext.__dataclass_params__.frozen,
        "RuntimeContext is frozen",
    )
    check(
        "JSON-SERIALIZATION",
        json.loads(runtime.to_json())[
            "repository_verified"
        ]
        is True,
        "RuntimeContext serializes",
    )
    check(
        "SYSPATH-UNIQUE",
        sys.path.count(str(root)) == 1,
        f"count={sys.path.count(str(root))}",
    )

    with tempfile.TemporaryDirectory() as temp:
        command = [
            sys.executable,
            str(root / "dev/run_genesis_ix_a5_pack1_audit.py"),
            "--database",
            str(Path(temp) / "missing.sqlite"),
            "--output-dir",
            str(Path(temp) / "audit"),
            "--show-runtime",
        ]

        completed = subprocess.run(
            command,
            cwd=temp,
            capture_output=True,
            text=True,
            timeout=120,
        )

        check(
            "ARBITRARY-CWD",
            completed.returncode == 0,
            completed.stderr.strip() or "launch succeeded",
        )
        check(
            "AUDIT-REPORT",
            (
                Path(temp)
                / "audit"
                / "retrieval_audit.json"
            ).is_file(),
            "report generated outside repository cwd",
        )

    failed = [
        item
        for item in checks
        if item["status"] != "PASS"
    ]
    status = "EXCELLENT" if not failed else "FAILED"

    output = (
        root
        / "docs/audits/genesis_ix_a5_pack1_1"
    )
    output.mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": "genesis_ix_a5_pack1_1_v1",
        "status": status,
        "runtime": runtime.to_dict(),
        "checks_executed": len(checks),
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "checks": checks,
    }

    (output / "bootstrap_certification.json").write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Genesis IX-A5 Pack 1.1 — Bootstrap Certification",
        "",
        f"**Status:** **{status}**",
        f"**Checks passed:** {report['checks_passed']}/{report['checks_executed']}",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]

    for item in checks:
        lines.append(
            f"| `{item['code']}` | **{item['status']}** | {item['detail']} |"
        )

    (output / "bootstrap_certification.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A5 PACK 1.1 — CANONICAL RUNTIME BOOTSTRAP")
    print("=" * 76)
    print("Checks executed :", report["checks_executed"])
    print("Checks passed   :", report["checks_passed"])
    print("Checks failed   :", report["checks_failed"])
    print("Overall status  :", status)
    print("=" * 76)

    return 0 if status == "EXCELLENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())

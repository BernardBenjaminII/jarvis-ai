#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

test -f core/cognition/__init__.py || {
    echo "ERROR: core/cognition/__init__.py not found."
    exit 1
}

test -f core/engineering/constitution.py || {
    echo "ERROR: Genesis V-E0 Engineering OS Foundation is required."
    exit 1
}

mkdir -p \
    dev/verification \
    docs/engineering \
    docs/audits \
    .artifacts/engineering \
    .migration_backups/genesis_5e1b

cat > dev/execute_genesis_5e1b_cognition_api_restoration.py <<'PYEOF'
#!/usr/bin/env python3
"""Execute the approved Genesis V-E1B cognition API restoration mission."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "core/cognition/__init__.py"
BACKUP_ROOT = ROOT / ".migration_backups/genesis_5e1b"

BEGIN = "# BEGIN GENESIS V-E1B MANAGED COGNITION EXPORTS"
END = "# END GENESIS V-E1B MANAGED COGNITION EXPORTS"

EXPORTS: dict[str, tuple[str, ...]] = {
    "core.cognition.workspace.catalog": (
        "CognitiveWorkspaceCatalog",
        "SortDirection",
        "WorkspaceQuery",
        "WorkspaceSortField",
    ),
    "core.cognition.workspace.enums": (
        "WorkspaceStatus",
    ),
    "core.cognition.workspace.models": (
        "Assumption",
        "EvidenceReference",
        "Hypothesis",
        "OpenQuestion",
    ),
    "core.cognition.workspace.repository": (
        "CognitiveWorkspaceCodec",
        "CognitiveWorkspaceConflictError",
        "CognitiveWorkspaceNotFoundError",
        "SQLiteCognitiveWorkspaceRepository",
    ),
    "core.cognition.workspace.service": (
        "CognitiveWorkspaceService",
    ),
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def validate_sources() -> None:
    """Prove every proposed symbol exists before modifying the public API."""
    failures: list[str] = []

    for module_name, expected_symbols in EXPORTS.items():
        module_path = ROOT / (module_name.replace(".", "/") + ".py")
        if not module_path.is_file():
            package_init = ROOT / module_name.replace(".", "/") / "__init__.py"
            module_path = package_init

        if not module_path.is_file():
            failures.append(f"Missing source module: {module_name}")
            continue

        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }

        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                definitions.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name != "*"
                )

        missing = sorted(set(expected_symbols) - definitions)
        if missing:
            failures.append(
                f"{module_name} does not expose expected definitions: {', '.join(missing)}"
            )

    if failures:
        raise RuntimeError(
            "Restoration preflight failed:\n- " + "\n- ".join(failures)
        )


def remove_managed_block(text: str) -> str:
    if BEGIN not in text:
        return text.rstrip() + "\n"

    before, remainder = text.split(BEGIN, 1)
    if END not in remainder:
        raise RuntimeError("Managed block begins but does not end")
    _, after = remainder.split(END, 1)
    return (before.rstrip() + "\n" + after.lstrip()).rstrip() + "\n"


def managed_block() -> str:
    names = tuple(
        sorted(
            symbol
            for symbols in EXPORTS.values()
            for symbol in symbols
        )
    )

    lines = [
        "",
        BEGIN,
        '"""Compatibility exports certified by Genesis V-E1B."""',
        "",
    ]

    for module_name, symbols in sorted(EXPORTS.items()):
        relative = module_name.removeprefix("core.cognition")
        lines.append(f"from .{relative.lstrip('.')} import (")
        for symbol in symbols:
            lines.append(f"    {symbol},")
        lines.append(")")
        lines.append("")

    lines.extend(
        [
            "try:",
            "    _existing_all = tuple(__all__)",
            "except NameError:",
            "    _existing_all = ()",
            "",
            "__all__ = tuple(",
            "    dict.fromkeys(",
            "        (*_existing_all,",
        ]
    )
    for name in names:
        lines.append(f'         "{name}",')
    lines.extend(
        [
            "        )",
            "    )",
            ")",
            "del _existing_all",
            END,
            "",
        ]
    )
    return "\n".join(lines)


def write_restoration() -> Path:
    original = TARGET.read_text(encoding="utf-8")
    timestamp = utc_stamp()
    backup_dir = BACKUP_ROOT / timestamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_path = backup_dir / "core_cognition___init__.py"
    shutil.copy2(TARGET, backup_path)

    restored = remove_managed_block(original) + managed_block()
    ast.parse(restored, filename=str(TARGET))
    TARGET.write_text(restored, encoding="utf-8")
    return backup_path


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def investigate_cognitive_object() -> Path:
    searches: list[dict[str, object]] = []

    commands = [
        [
            "git",
            "grep",
            "-n",
            "-E",
            r"class CognitiveObject|CognitiveObject[[:space:]]*=",
            "--",
            "*.py",
        ],
        [
            "git",
            "log",
            "--all",
            "--oneline",
            "--decorate",
            "-S",
            "class CognitiveObject",
            "--",
            "core",
        ],
        [
            "git",
            "log",
            "--all",
            "--oneline",
            "--decorate",
            "-S",
            "CognitiveObject",
            "--",
            "core/cognition",
            "tests",
        ],
    ]

    for command in commands:
        result = run_command(command)
        searches.append(
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )

    current_path = ROOT / "core/cognition/common/cognitive_object.py"
    current_source = (
        current_path.read_text(encoding="utf-8")
        if current_path.is_file()
        else None
    )

    payload = {
        "schema_version": 1,
        "subject": "core.cognition.common.cognitive_object.CognitiveObject",
        "current_file_exists": current_path.is_file(),
        "current_file": str(current_path.relative_to(ROOT)),
        "current_source": current_source,
        "searches": searches,
        "decision": (
            "NO_AUTOMATIC_CHANGE: implementation identity is not sufficiently proven."
        ),
    }

    json_path = ROOT / ".artifacts/engineering/cognitive_object_archaeology.json"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report_path = ROOT / "docs/audits/cognitive_object_archaeology.md"
    lines = [
        "# CognitiveObject Repository Archaeology",
        "",
        "**Subject:** `core.cognition.common.cognitive_object.CognitiveObject`",
        "",
        "## Decision",
        "",
        "**NO AUTOMATIC CHANGE**",
        "",
        "The Engineering OS did not find enough certified evidence to restore, rename,",
        "or recreate `CognitiveObject` automatically.",
        "",
        "## Current Repository State",
        "",
        f"- File exists: `{current_path.is_file()}`",
        f"- Path: `{current_path.relative_to(ROOT)}`",
        "",
    ]

    if current_source is not None:
        lines.extend(
            [
                "### Current source",
                "",
                "```python",
                current_source.rstrip(),
                "```",
                "",
            ]
        )

    lines.extend(["## Git Evidence", ""])
    for item in searches:
        command = " ".join(item["command"])
        lines.extend(
            [
                f"### `{command}`",
                "",
                f"- Return code: `{item['returncode']}`",
                "",
                "```text",
                str(item["stdout"] or item["stderr"] or "(no matches)"),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Required Commander Decision",
            "",
            "Choose one only after reviewing the evidence:",
            "",
            "1. Restore the historical `CognitiveObject` contract.",
            "2. Update stale tests to the certified replacement contract.",
            "3. Add an explicit compatibility alias to a proven successor.",
            "",
            "No source change was made for this unresolved symbol.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    validate_sources()
    backup_path = write_restoration()
    archaeology_path = investigate_cognitive_object()

    print(f"[PASS] Restored 14 cognition public exports")
    print(f"[PASS] Backup created: {backup_path.relative_to(ROOT)}")
    print(f"[PASS] CognitiveObject archaeology: {archaeology_path.relative_to(ROOT)}")
    print("[PASS] Unresolved symbol left unchanged pending evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verification/verify_genesis_5e1b_cognition_api_restoration.py <<'PYEOF'
#!/usr/bin/env python3
"""Verify Genesis V-E1B cognition API restoration."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = (
    "Assumption",
    "CognitiveWorkspaceCatalog",
    "CognitiveWorkspaceCodec",
    "CognitiveWorkspaceConflictError",
    "CognitiveWorkspaceNotFoundError",
    "CognitiveWorkspaceService",
    "EvidenceReference",
    "Hypothesis",
    "OpenQuestion",
    "SQLiteCognitiveWorkspaceRepository",
    "SortDirection",
    "WorkspaceQuery",
    "WorkspaceSortField",
    "WorkspaceStatus",
)


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def main() -> int:
    failures = 0

    cognition = importlib.import_module("core.cognition")
    failures += check(
        all(hasattr(cognition, name) for name in EXPECTED),
        "Fourteen cognition compatibility exports",
    )
    failures += check(
        all(name in cognition.__all__ for name in EXPECTED),
        "Cognition __all__ compatibility surface",
    )

    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/cognition",
            "dev/execute_genesis_5e1b_cognition_api_restoration.py",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(
        compile_result.returncode == 0,
        "Restored cognition compilation",
    )

    analysis = subprocess.run(
        ["bash", "dev/analyze_public_api_compatibility.sh"],
        cwd=ROOT,
        check=False,
        env={
            **__import__("os").environ,
            "PYTHON_BIN": sys.executable,
        },
    )
    failures += check(
        analysis.returncode == 0,
        "Compatibility analyzer execution",
    )

    evidence_path = ROOT / ".artifacts/engineering/public_api_compatibility.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    findings = evidence.get("findings", [])

    cognition_export_findings = [
        item
        for item in findings
        if item.get("package") == "core.cognition"
    ]
    failures += check(
        not cognition_export_findings,
        "All core.cognition missing exports resolved",
    )

    unresolved = [
        item
        for item in findings
        if item.get("package") == "core.cognition.common.cognitive_object"
        and item.get("symbol") == "CognitiveObject"
    ]
    failures += check(
        len(unresolved) <= 1,
        "CognitiveObject remains a single governed investigation",
    )

    archaeology = ROOT / "docs/audits/cognitive_object_archaeology.md"
    failures += check(
        archaeology.is_file()
        and "NO AUTOMATIC CHANGE" in archaeology.read_text(encoding="utf-8"),
        "CognitiveObject archaeology evidence",
    )

    ve1a = subprocess.run(
        [sys.executable, "dev/verification/verify_genesis_5e1a_repository_reality_modeling.py"],
        cwd=ROOT,
        check=False,
    )
    failures += check(
        ve1a.returncode == 0,
        "Genesis V-E1A regression",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_5e1b.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E1B — COGNITION API RESTORATION"
echo "========================================================================"

"${PYTHON_BIN}" dev/verification/verify_genesis_5e1b_cognition_api_restoration.py
SHEOF

cat > docs/engineering/genesis_v_e1b_cognition_api_restoration.md <<'EOF'
# Genesis V-E1B — Cognition API Restoration

## Mission

Use the Engineering OS compatibility evidence to restore verified public API
exports in `core.cognition` while refusing to invent an implementation for the
unresolved `CognitiveObject` contract.

## Approved Remediation

Fourteen symbols already implemented in the cognition workspace subsystem are
re-exported through `core.cognition`.

The implementation remains canonical in its existing modules. No duplicate
classes, services, repositories, codecs, enums, or query contracts are created.

## Governed Exception

`core.cognition.common.cognitive_object.CognitiveObject` is not restored
automatically.

The Engineering OS performs repository and Git archaeology, writes evidence to:

- `.artifacts/engineering/cognitive_object_archaeology.json`
- `docs/audits/cognitive_object_archaeology.md`

A Commander decision is required if the evidence does not prove the correct
historical or replacement contract.

## Completion Criterion

The phase is complete when:

1. all fourteen `core.cognition` missing-export findings disappear;
2. the analyzer completes successfully;
3. `CognitiveObject` is represented by no more than one governed finding;
4. V-E1A and earlier Engineering OS regressions pass.
EOF

chmod +x \
    dev/execute_genesis_5e1b_cognition_api_restoration.py \
    dev/verification/verify_genesis_5e1b_cognition_api_restoration.py \
    dev/verify_genesis_5e1b.sh

"${PYTHON_BIN}" dev/execute_genesis_5e1b_cognition_api_restoration.py
"${PYTHON_BIN}" dev/verification/verify_genesis_5e1b_cognition_api_restoration.py

echo
echo "Genesis V-E1B installed, executed, and verified."
echo
echo "Review the unresolved-symbol evidence:"
echo "  cat docs/audits/cognitive_object_archaeology.md"

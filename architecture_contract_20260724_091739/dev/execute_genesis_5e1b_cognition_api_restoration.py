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

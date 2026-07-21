#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

COMMON_ROOT="${PROJECT_ROOT}/core/cognition/common"
MODULES=(
    "contracts"
    "errors"
    "normalization"
    "serialization"
)

banner() {
    printf '\n======================================================================\n'
    printf '%s\n' "$1"
    printf '======================================================================\n\n'
}

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

[[ -d "$COMMON_ROOT" ]] || fail "Missing common package: $COMMON_ROOT"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || [[ -x "$PYTHON_BIN" ]] \
    || fail "Python interpreter not found: $PYTHON_BIN"

banner "JARVIS GENESIS IV-R0-B — RELATIVE IMPORT REPAIR"

PROJECT_ROOT="$PROJECT_ROOT" "$PYTHON_BIN" - <<'PYEOF'
from __future__ import annotations

import os
import re
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"]).resolve()
common_root = project_root / "core" / "cognition" / "common"

common_modules = {
    "contracts",
    "errors",
    "normalization",
    "serialization",
}

targets = tuple(common_root / f"{name}.py" for name in sorted(common_modules))

for path in targets:
    if not path.is_file():
        raise SystemExit(f"Missing migrated module: {path}")

    original = path.read_text(encoding="utf-8")
    repaired_lines: list[str] = []

    for line in original.splitlines(keepends=True):
        # Match ordinary single-dot relative imports such as:
        #   from .enums import ...
        #   from .contracts import ...
        match = re.match(
            r"^(?P<indent>\s*)from \.(?P<module>[A-Za-z_][A-Za-z0-9_\.]*) import ",
            line,
        )

        if match:
            root_module = match.group("module").split(".", 1)[0]

            # Imports between modules now colocated in common/ remain single-dot.
            # Imports targeting modules still in core/cognition move up one level.
            if root_module not in common_modules:
                prefix_end = match.end("indent")
                line = (
                    line[:prefix_end]
                    + "from .."
                    + line[match.end("indent") + len("from ."):]
                )

        # Handle `from . import name` by moving to the cognition parent package.
        line = re.sub(r"^(\s*)from \. import ", r"\1from .. import ", line)

        repaired_lines.append(line)

    repaired = "".join(repaired_lines)

    if repaired != original:
        path.write_text(repaired, encoding="utf-8")
        print(f"[PASS] Repaired {path.relative_to(project_root)}")
    else:
        print(f"[SKIP] No import-depth changes needed: {path.relative_to(project_root)}")
PYEOF

"$PYTHON_BIN" -m compileall -q \
    "${PROJECT_ROOT}/core/cognition/common" \
    "${PROJECT_ROOT}/core/cognition/contracts.py" \
    "${PROJECT_ROOT}/core/cognition/errors.py" \
    "${PROJECT_ROOT}/core/cognition/normalization.py" \
    "${PROJECT_ROOT}/core/cognition/serialization.py"

pass "Common infrastructure compilation"

PROJECT_ROOT="$PROJECT_ROOT" "$PYTHON_BIN" - <<'PYEOF'
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"]).resolve()
sys.path.insert(0, str(project_root))

modules = ("contracts", "errors", "normalization", "serialization")

for module_name in modules:
    canonical = importlib.import_module(f"core.cognition.common.{module_name}")
    legacy = importlib.import_module(f"core.cognition.{module_name}")

    canonical_exports = tuple(getattr(canonical, "__all__", ()))
    legacy_exports = tuple(getattr(legacy, "__all__", ()))

    if canonical_exports != legacy_exports:
        raise AssertionError(
            f"{module_name}: canonical and legacy __all__ differ"
        )

    for export_name in canonical_exports:
        canonical_value = getattr(canonical, export_name)
        legacy_value = getattr(legacy, export_name)

        if canonical_value is not legacy_value:
            raise AssertionError(
                f"{module_name}: export identity differs for {export_name!r}"
            )

importlib.import_module("core.cognition")

print("[PASS] Canonical common imports")
print("[PASS] Legacy compatibility imports")
print("[PASS] Export identity preservation")
print("[PASS] Existing cognition facade")
PYEOF

if [[ -d "${PROJECT_ROOT}/tests/cognition" ]]; then
    "$PYTHON_BIN" -m unittest discover \
        -s "${PROJECT_ROOT}/tests/cognition" \
        -t "${PROJECT_ROOT}" \
        -p 'test_*.py'
    pass "Cognition regression tests"
fi

banner "GENESIS IV-R0-B IMPORT REPAIR COMPLETE"

printf 'Repaired location : core/cognition/common/\n'
printf 'Public API intent : Unchanged\n'
printf 'Overall status    : EXCELLENT\n'

#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

COGNITION_ROOT="${PROJECT_ROOT}/core/cognition"
COMMON_ROOT="${COGNITION_ROOT}/common"
BACKUP_ROOT="${PROJECT_ROOT}/.migration_backups/genesis_4r0b_$(date +%Y%m%d_%H%M%S)"

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
skip() { printf '[SKIP] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

require_file() {
    [[ -f "$1" ]] || fail "Required file missing: ${1#${PROJECT_ROOT}/}"
}

is_compatibility_shim() {
    grep -q "GENESIS IV-R0-B COMPATIBILITY SHIM" "$1" 2>/dev/null
}

write_common_init() {
    cat > "${COMMON_ROOT}/__init__.py" <<'PYEOF'
"""
Shared deterministic infrastructure for the JARVIS cognition subsystem.

Genesis IV-R0-B establishes this package as the dependency floor for cognition
layers. Concrete symbols remain available through their module-specific paths.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
PYEOF
}

write_shim() {
    local module="$1"
    cat > "${COGNITION_ROOT}/${module}.py" <<PYEOF
"""
GENESIS IV-R0-B COMPATIBILITY SHIM

The canonical implementation moved to:
    core.cognition.common.${module}

This module preserves the established import path:
    core.cognition.${module}
"""

from __future__ import annotations

from .common.${module} import *  # noqa: F401,F403
from .common.${module} import __all__ as __all__
PYEOF
}

ensure_module_all() {
    local file="$1"

    if grep -Eq '^__all__[[:space:]]*[:=]' "$file"; then
        return
    fi

    cat >> "$file" <<'PYEOF'


# Public names retained for compatibility with the pre-R0-B module path.
__all__: tuple[str, ...] = tuple(
    name
    for name in globals()
    if not name.startswith("_")
)
PYEOF
}

preflight() {
    [[ -d "$PROJECT_ROOT" ]] || fail "Project root does not exist: $PROJECT_ROOT"
    [[ -d "$COGNITION_ROOT" ]] || fail "Cognition package not found: $COGNITION_ROOT"
    command -v "$PYTHON_BIN" >/dev/null 2>&1 || [[ -x "$PYTHON_BIN" ]] \
        || fail "Python interpreter not found: $PYTHON_BIN"

    require_file "${COGNITION_ROOT}/__init__.py"
    mkdir -p "$COMMON_ROOT"

    for module in "${MODULES[@]}"; do
        local legacy="${COGNITION_ROOT}/${module}.py"
        local canonical="${COMMON_ROOT}/${module}.py"

        if [[ ! -f "$legacy" && ! -f "$canonical" ]]; then
            fail "Neither legacy nor canonical module exists for: ${module}"
        fi

        if [[ -f "$legacy" ]] && is_compatibility_shim "$legacy" && [[ ! -f "$canonical" ]]; then
            fail "Incomplete prior migration for ${module}"
        fi
    done
}

migrate_modules() {
    mkdir -p "$BACKUP_ROOT"

    for module in "${MODULES[@]}"; do
        local legacy="${COGNITION_ROOT}/${module}.py"
        local canonical="${COMMON_ROOT}/${module}.py"

        if [[ -f "$canonical" ]] && [[ -f "$legacy" ]] && is_compatibility_shim "$legacy"; then
            skip "${module}.py already migrated"
            continue
        fi

        require_file "$legacy"

        cp -a "$legacy" "${BACKUP_ROOT}/${module}.py"
        cp -a "$legacy" "$canonical"
        ensure_module_all "$canonical"
        write_shim "$module"

        pass "Migrated ${module}.py with compatibility shim"
    done

    write_common_init
    pass "Canonical common package initializer"
}

verify_structure() {
    require_file "${COMMON_ROOT}/__init__.py"

    for module in "${MODULES[@]}"; do
        require_file "${COMMON_ROOT}/${module}.py"
        require_file "${COGNITION_ROOT}/${module}.py"
        is_compatibility_shim "${COGNITION_ROOT}/${module}.py" \
            || fail "Legacy module is not an R0-B shim: core/cognition/${module}.py"
    done

    pass "R0-B migration structure"
}

verify_compilation() {
    "$PYTHON_BIN" -m compileall -q \
        "${COMMON_ROOT}" \
        "${COGNITION_ROOT}/contracts.py" \
        "${COGNITION_ROOT}/errors.py" \
        "${COGNITION_ROOT}/normalization.py" \
        "${COGNITION_ROOT}/serialization.py"

    pass "Common infrastructure compilation"
}

verify_imports() {
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
    legacy = importlib.import_module(f"core.cognition.{module_name}")
    canonical = importlib.import_module(f"core.cognition.common.{module_name}")

    legacy_exports = tuple(getattr(legacy, "__all__", ()))
    canonical_exports = tuple(getattr(canonical, "__all__", ()))

    if legacy_exports != canonical_exports:
        raise AssertionError(
            f"{module_name}: legacy and canonical __all__ differ"
        )

    for export_name in canonical_exports:
        if not hasattr(legacy, export_name):
            raise AssertionError(
                f"{module_name}: legacy module lost export {export_name!r}"
            )
        if getattr(legacy, export_name) is not getattr(canonical, export_name):
            raise AssertionError(
                f"{module_name}: export identity changed for {export_name!r}"
            )

importlib.import_module("core.cognition")

print("[PASS] Canonical and legacy imports")
print("[PASS] Export identity preservation")
print("[PASS] Existing cognition facade")
PYEOF
}

verify_tests() {
    if [[ -d "${PROJECT_ROOT}/tests/cognition" ]]; then
        "$PYTHON_BIN" -m unittest discover \
            -s "${PROJECT_ROOT}/tests/cognition" \
            -t "${PROJECT_ROOT}" \
            -p 'test_*.py'
        pass "Cognition regression tests"
    else
        skip "tests/cognition not present"
    fi
}

main() {
    banner "JARVIS GENESIS IV-R0-B — COMMON INFRASTRUCTURE MIGRATION"

    printf 'Project root : %s\n' "$PROJECT_ROOT"
    printf 'Python       : %s\n' "$PYTHON_BIN"
    printf 'Backup       : %s\n\n' "$BACKUP_ROOT"

    preflight
    pass "Migration preflight"

    migrate_modules
    verify_structure
    verify_compilation
    verify_imports
    verify_tests

    banner "GENESIS IV-R0-B MIGRATION COMPLETE"

    printf 'Canonical location : core/cognition/common/\n'
    printf 'Compatibility paths: core/cognition/{contracts,errors,normalization,serialization}.py\n'
    printf 'Backup location    : %s\n' "$BACKUP_ROOT"
    printf 'Behavioral intent  : No public API changes\n'
    printf 'Overall status     : EXCELLENT\n'
}

main "$@"

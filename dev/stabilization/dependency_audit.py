#!/usr/bin/env python3

from __future__ import annotations

import ast
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "archive",
}

requirements_dir = ROOT / "requirements"

# --------------------------------------------------------
# Gather local packages
# --------------------------------------------------------

local_modules = set()

for path in ROOT.iterdir():

    if path.name.startswith("."):
        continue

    if path.name in IGNORE_DIRS:
        continue

    if path.is_dir():

        if (path / "__init__.py").exists():
            local_modules.add(path.name)

    elif path.suffix == ".py":

        local_modules.add(path.stem)

# --------------------------------------------------------
# Python standard library
# --------------------------------------------------------

stdlib = set(sys.stdlib_module_names)

# --------------------------------------------------------
# Parse imports
# --------------------------------------------------------

imports = defaultdict(set)

for py in ROOT.rglob("*.py"):

    if any(part in IGNORE_DIRS for part in py.parts):
        continue

    try:
        tree = ast.parse(py.read_text(encoding="utf-8"))
    except Exception:
        continue

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imports[alias.name.split(".")[0]].add(py)

        elif isinstance(node, ast.ImportFrom):

            if node.module:

                imports[node.module.split(".")[0]].add(py)

# --------------------------------------------------------
# Read requirements
# --------------------------------------------------------

declared = set()

for txt in requirements_dir.glob("*.txt"):

    for line in txt.read_text().splitlines():

        line = line.strip()

        if (
            not line
            or line.startswith("#")
            or line.startswith("-r")
        ):
            continue

        pkg = (
            line.split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split("[")[0]
            .strip()
            .lower()
        )

        declared.add(pkg)

# --------------------------------------------------------
# Classify
# --------------------------------------------------------

third_party = set()
stdlib_found = set()
local_found = set()
unknown = set()

for module in imports:

    lower = module.lower()

    if module in stdlib:
        stdlib_found.add(module)

    elif module in local_modules:
        local_found.add(module)

    else:
        third_party.add(lower)

# --------------------------------------------------------
# Report
# --------------------------------------------------------

print("=" * 72)
print("JARVIS DEPENDENCY AUDIT")
print("=" * 72)

print("\nSTANDARD LIBRARY\n")

for x in sorted(stdlib_found):
    print(" ", x)

print("\nLOCAL MODULES\n")

for x in sorted(local_found):
    print(" ", x)

print("\nTHIRD PARTY IMPORTS\n")

for x in sorted(third_party):
    flag = "✓" if x in declared else "MISSING"

    print(f"{flag:8} {x}")

print("\nSUMMARY")
print("-" * 72)
print("Stdlib       :", len(stdlib_found))
print("Local        :", len(local_found))
print("Third Party  :", len(third_party))
print("Requirements :", len(declared))

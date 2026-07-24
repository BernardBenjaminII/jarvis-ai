#!/usr/bin/env python3

from __future__ import annotations

import ast
import sys
from pathlib import Path
from collections import defaultdict
from importlib import metadata

ROOT = Path(__file__).resolve().parents[2]

IGNORE = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "archive",
    "node_modules",
}

NAMESPACE_IMPORTS_TO_IGNORE = {
    "google",
}

########################################################################
# Python knows this mapping already
########################################################################

PACKAGE_MAP = {}

for module, dists in metadata.packages_distributions().items():

    if dists:
        PACKAGE_MAP[module] = dists[0]

########################################################################
# Discover local modules
########################################################################

LOCAL = set()

for path in ROOT.rglob("*"):

    if any(x in IGNORE for x in path.parts):
        continue

    if path.is_dir():

        py_files = list(path.glob("*.py"))

        if py_files:
            LOCAL.add(path.name)

    elif path.suffix == ".py":

        LOCAL.add(path.stem)

########################################################################
# Read requirements
########################################################################

DECLARED = defaultdict(set)

for req in (ROOT / "requirements").glob("*.txt"):

    for line in req.read_text().splitlines():

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
            .strip()
            .lower()
        )

        DECLARED[pkg].add(req.name)

########################################################################
# Scan imports
########################################################################

imports = defaultdict(set)

for py in ROOT.rglob("*.py"):

    if any(x in IGNORE for x in py.parts):
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

            if node.level:

                continue

            if node.module:

                imports[node.module.split(".")[0]].add(py)

########################################################################
# Classify
########################################################################

stdlib = set(sys.stdlib_module_names)

print("=" * 80)
print("JARVIS DEPENDENCY MANAGER")
print("=" * 80)

third = {}

for module in sorted(imports):

    lower = module.lower()

    if module in stdlib:

        continue

    if module in LOCAL:

        continue

    if module in NAMESPACE_IMPORTS_TO_IGNORE:

        continue

    package = PACKAGE_MAP.get(module)

    if package is None:

        package = module

    third[module] = package

########################################################################
# Installed packages
########################################################################

installed = {}

for dist in metadata.distributions():

    name = dist.metadata["Name"]

    installed[name.lower()] = dist.version

########################################################################
# Report
########################################################################

missing_requirements = []

missing_packages = []

print()

for module, package in sorted(third.items()):

    pkg = package.lower()

    declared = pkg in DECLARED

    installed_ok = pkg in installed

    status = []

    if declared:
        status.append("REQ")
    else:
        status.append("NO_REQ")
        missing_requirements.append(package)

    if installed_ok:
        status.append("INSTALLED")
    else:
        status.append("NOT_INSTALLED")
        missing_packages.append(package)

    print(
        f"{module:30}"
        f"{package:35}"
        f"{' '.join(status)}"
    )

print()

print("=" * 80)

print("Missing requirements:")

for pkg in sorted(set(missing_requirements)):

    print(" ", pkg)

print()

print("Missing packages:")

for pkg in sorted(set(missing_packages)):

    print(" ", pkg)

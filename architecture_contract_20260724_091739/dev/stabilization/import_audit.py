#!/usr/bin/env python3

from pathlib import Path
import ast
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]

IGNORE = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "archive",
}

imports = defaultdict(set)


def top_module(name):
    return name.split(".")[0]


for py in ROOT.rglob("*.py"):

    if any(part in IGNORE for part in py.parts):
        continue

    try:
        tree = ast.parse(py.read_text(encoding="utf-8"))
    except Exception:
        continue

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imports[top_module(alias.name)].add(py)

        elif isinstance(node, ast.ImportFrom):

            if node.module:

                imports[top_module(node.module)].add(py)


print("=" * 70)

print("JARVIS IMPORT AUDIT")

print("=" * 70)

for module in sorted(imports):

    print(f"{module:25} {len(imports[module]):4} files")

print()

print(f"Unique modules: {len(imports)}")

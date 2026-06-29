from __future__ import annotations

import ast
import importlib.util
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

IGNORE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "node_modules", "archive"
}


def ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def resolve_relative(current_module: str, level: int, module: str | None) -> str:
    parts = current_module.split(".")[:-1]
    if level:
        parts = parts[: max(0, len(parts) - level + 1)]
    if module:
        parts.extend(module.split("."))
    return ".".join(parts)


def import_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


class ArchitectureReport:
    def __init__(self):
        self.imports = []
        self.dependencies = defaultdict(set)

    def scan(self):
        for path in ROOT.rglob("*.py"):
            if ignored(path):
                continue
            self.scan_file(path)

    def scan_file(self, path: Path):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception as exc:
            print(f"[WARN] Could not parse {path.relative_to(ROOT)}: {exc}")
            return

        current = module_name(path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append((current, alias.name, path, node.lineno))
                    self.dependencies[current].add(alias.name)

            elif isinstance(node, ast.ImportFrom):
                dep = resolve_relative(current, node.level, node.module)
                self.imports.append((current, dep, path, node.lineno))
                self.dependencies[current].add(dep)

    def print_report(self):
        self.scan()

        print("\nARCHITECTURE")
        print("=" * 70)
        print(f"Python modules : {len(self.dependencies)}")
        print(f"Imports        : {len(self.imports)}")

        print("\nOLD core.src IMPORTS")
        print("-" * 70)
        found = False
        for current, dep, path, line in self.imports:
            if dep.startswith("core.src"):
                found = True
                print(f"{path.relative_to(ROOT)}:{line}")
                print(f"  {current} -> {dep}")
        if not found:
            print("None")

        print("\nBROKEN LOCAL IMPORTS")
        print("-" * 70)
        found = False
        for current, dep, path, line in self.imports:
            if not dep.startswith(("core", "tools", "capabilities", "launcher", "config")):
                continue
            if not import_exists(dep):
                found = True
                print(f"{path.relative_to(ROOT)}:{line}")
                print(f"  {current} -> {dep}")
        if not found:
            print("None detected")

        print("\nCORE PACKAGE DEPENDENCIES")
        print("-" * 70)
        graph = defaultdict(set)

        for current, deps in self.dependencies.items():
            if not current.startswith("core."):
                continue

            current_parts = current.split(".")
            if len(current_parts) < 2:
                continue

            current_pkg = ".".join(current_parts[:2])

            for dep in deps:
                if dep.startswith("core."):
                    dep_parts = dep.split(".")
                    if len(dep_parts) >= 2:
                        dep_pkg = ".".join(dep_parts[:2])
                        if dep_pkg != current_pkg:
                            graph[current_pkg].add(dep_pkg)

        for pkg in sorted(graph):
            print(pkg)
            for dep in sorted(graph[pkg]):
                print(f"  -> {dep}")


def run():
    ArchitectureReport().print_report()

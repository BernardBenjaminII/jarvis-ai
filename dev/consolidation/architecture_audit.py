from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
# ------------------------------------------------------------------
# Bootstrap Architecture
#
# Entry Points
#     Public interfaces into the Bootstrap subsystem.
#
# Orchestrators
#     High-level coordination components.
#
# Execution
#     Runtime execution pipeline.
#
# Services
#     Individual bootstrap service implementations.
# ------------------------------------------------------------------
GROUPS = {
    "bootstrap_entrypoints": [
    "core/bootstrap/main.py",
    "core/bootstrap/runner.py",
    ],

    "bootstrap_orchestrators": [
        "core/bootstrap/bootstrap.py",
    ],

    "bootstrap_execution": [
        "core/bootstrap/preflight_runner.py",
        "core/bootstrap/lifecycle_runner.py",
    ],

    "bootstrap_services": [
        "core/bootstrap/runtime.py",
        "core/bootstrap/runtime_check.py",
        "core/bootstrap/api.py",
        "core/bootstrap/capabilities.py",
        "core/bootstrap/dependencies.py",
        "core/bootstrap/models.py",
        "core/bootstrap/ollama.py",
        "core/bootstrap/venv.py",
    ],

    "workflow_layers": [
        "knowledge_engine/workflow",
        "knowledge_engine/workflows",
        "knowledge_engine/orchestrator",
        "knowledge_engine/director",
    ],
    "processing_layers": [
        "knowledge_engine/processing",
        "knowledge_engine/processors",
    ],
    "discovery_layers": [
        "knowledge_engine/discovery",
        "knowledge_engine/capabilities/discovery.py",
    ],
    "backup_files": [
        "*.bak",
        "*.pre_resource_refactor.bak",
        "*.resource_v1.bak",
        "*.resource_working.bak",
        "*.monolith.bak",
    ],
}


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def find_backups() -> list[Path]:
    results: list[Path] = []
    for pattern in GROUPS["backup_files"]:
        results.extend(ROOT.rglob(pattern))
    return sorted(set(results))


def main() -> int:
    print("\nJARVIS Phase II-A Architecture Audit")
    print("=" * 50)

    for group, paths in GROUPS.items():
        if group == "backup_files":
            continue

        print(f"\n[{group}]")
        for item in paths:
            status = "FOUND" if exists(item) else "missing"
            print(f"{status:8} {item}")

    backups = find_backups()

    print("\n[backup_files]")
    if not backups:
        print("No backup files found.")
    else:
        for path in backups:
            print(path.relative_to(ROOT))

    print("\nAudit complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

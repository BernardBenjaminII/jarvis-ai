from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]

BLUEPRINT = ROOT / "docs" / "architecture" / "architecture_blueprint.md"

REQUIRED_PATHS = [
    "core/bootstrap",
    "core/bootstrap/main.py",
    "core/bootstrap/discovery",
    "core/bootstrap/services",
    "knowledge_engine",
    "knowledge_engine/receiving",
    "knowledge_engine/discovery",
    "knowledge_engine/inspectors",
    "knowledge_engine/extraction",
    "knowledge_engine/processing",
    "knowledge_engine/processors",
    "knowledge_engine/chunking",
    "knowledge_engine/embeddings",
    "knowledge_engine/objects",
    "knowledge_engine/registry",
    "knowledge_engine/knowledge_graph",
    "knowledge_engine/retrieval",
    "knowledge_engine/validation",
    "knowledge_engine/promotion",
    "knowledge_engine/queue",
    "knowledge_engine/workflow",
    "knowledge_engine/workflows",
    "knowledge_engine/orchestrator",
    "knowledge_engine/director",
    "knowledge_engine/capabilities",
    "dev/librarian",
    "dev/verify",
]

REQUIRED_BLUEPRINT_TERMS = [
    "Bootstrap",
    "Runtime",
    "Core Services",
    "Capability Framework",
    "Knowledge Engine",
    "Librarian",
]

def check_blueprint_exists() -> int:
    if BLUEPRINT.exists():
        print(f"[PASS] Blueprint exists: {BLUEPRINT.relative_to(ROOT)}")
        return 0

    print(f"[FAIL] Missing blueprint: {BLUEPRINT.relative_to(ROOT)}")
    return 1


def check_required_paths() -> int:
    failures = 0

    print("\nRequired architecture paths")
    print("-" * 40)

    for rel in REQUIRED_PATHS:
        path = ROOT / rel
        if path.exists():
            print(f"[PASS] {rel}")
        else:
            print(f"[FAIL] {rel}")
            failures += 1

    return failures


def check_blueprint_terms() -> int:
    failures = 0

    print("\nBlueprint section verification")
    print("-" * 40)

    if not BLUEPRINT.exists():
        print("[FAIL] Missing blueprint.")
        return 1

    text = BLUEPRINT.read_text(encoding="utf-8", errors="replace")
    text_lower = text.lower()

    REQUIRED_SECTIONS = [
        ("Receiving", "receiving"),
        ("Discovery", "discovery"),
        ("Inspection", "inspection"),
        ("Extraction", "extraction"),
        ("Processing", "processing"),
        ("Chunking", "chunking"),
        ("Embeddings", "embeddings"),
        ("Objects", "objects"),
        ("Registry", "registry"),
        ("Knowledge Graph", "knowledge graph"),
        ("Retrieval", "retrieval"),
        ("Workflow", "workflow"),
        ("Director", "director"),
        ("Orchestrator", "orchestrator"),
    ]

    for display, token in REQUIRED_SECTIONS:
        if token in text_lower:
            print(f"[PASS] {display}")
        else:
            print(f"[FAIL] {display}")
            failures += 1

    return failures

def main() -> int:
    print("\nJARVIS Architecture Blueprint Verification")
    print("=" * 50)

    failures = 0
    failures += check_blueprint_exists()
    failures += check_required_paths()
    failures += check_blueprint_terms()

    print("\nResult")
    print("-" * 40)

    if failures:
        print(f"[FAIL] Architecture blueprint verification failed with {failures} issue(s).")
        return 1

    print("[PASS] Architecture blueprint verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

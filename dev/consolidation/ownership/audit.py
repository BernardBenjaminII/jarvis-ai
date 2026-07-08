from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

TARGETS = [
    "knowledge_engine/processing",
    "knowledge_engine/processors",
    "knowledge_engine/workflow",
    "knowledge_engine/workflows",
    "knowledge_engine/orchestrator",
    "knowledge_engine/director",
    "knowledge_engine/discovery",
    "knowledge_engine/capabilities",
]

print("\nJARVIS Ownership Audit")
print("=" * 60)

for target in TARGETS:
    path = ROOT / target

    print(f"\n{target}")
    print("-" * len(target))

    if not path.exists():
        print("Missing")
        continue

    py_files = sorted(path.rglob("*.py"))

    print(f"Python files: {len(py_files)}")

    for file in py_files:
        rel = file.relative_to(ROOT)
        print(f"  - {rel}")

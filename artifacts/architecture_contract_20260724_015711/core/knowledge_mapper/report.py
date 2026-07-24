from pathlib import Path

from core.knowledge_mapper.indexer import build_subject_index


def print_summary(root: Path):

    index = build_subject_index(root)

    print()

    print("=" * 60)
    print("KNOWLEDGE MAPPER SUMMARY")
    print("=" * 60)

    print()

    for subject in sorted(index):

        print(f"{subject:30} {len(index[subject]):5d}")

    print()

    print(f"Mapped Subjects : {len(index)}")

    print(
        f"Mapped Files    : {sum(len(v) for v in index.values())}"
    )

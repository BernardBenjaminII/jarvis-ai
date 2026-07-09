from pathlib import Path

from knowledge_engine.receiving.filters import should_ignore


def scan(root: str):

    accepted = []
    rejected = []

    root = Path(root)

    for path in root.rglob("*"):

        ignore, reason = should_ignore(path)

        if ignore:
            rejected.append((path, reason))
            continue

        accepted.append(path)

    return accepted, rejected

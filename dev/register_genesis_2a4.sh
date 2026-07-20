#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

python3 <<'PY'
from pathlib import Path

anchor = "dev/verify_genesis_2a3a.sh"
new_entry = "dev/verify_genesis_2a4.sh"

if not Path(new_entry).is_file():
    raise SystemExit(f"ERROR: Missing verifier: {new_entry}")

candidates: list[Path] = []

for path in Path("dev").rglob("*"):
    if not path.is_file():
        continue

    if path.name in {
        "verify_genesis_all.sh",
        "verify_genesis_2a3a.sh",
        "register_genesis_2a4.sh",
    }:
        continue

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue

    lines = [line.strip() for line in text.splitlines()]

    if anchor in lines:
        candidates.append(path)

if len(candidates) != 1:
    details = "\n".join(f"  - {path}" for path in candidates) or "  none"
    raise SystemExit(
        "ERROR: Expected exactly one Genesis verifier manifest containing "
        f"{anchor!r}.\nFound:\n{details}"
    )

manifest = candidates[0]
text = manifest.read_text(encoding="utf-8")
lines = text.splitlines()

if new_entry in [line.strip() for line in lines]:
    print(f"[UNCHANGED] {new_entry} already registered in {manifest}")
else:
    output: list[str] = []
    inserted = False

    for line in lines:
        output.append(line)

        if line.strip() == anchor:
            output.append(new_entry)
            inserted = True

    if not inserted:
        raise SystemExit(
            f"ERROR: Anchor disappeared while editing {manifest}"
        )

    manifest.write_text(
        "\n".join(output) + "\n",
        encoding="utf-8",
    )

    print(f"[UPDATED] Registered {new_entry} in {manifest}")

print(f"[MANIFEST] {manifest}")
PY

echo
echo "Genesis II-A4 registration complete."

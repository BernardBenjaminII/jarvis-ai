#!/usr/bin/env python3
"""Generate the deterministic Genesis IV-B4 migration report."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.observation.audit import (  # noqa: E402
    audit_observation_definitions,
)
from core.observation.migration_registry import (  # noqa: E402
    MIGRATION_ENTRIES,
    MIGRATION_SCHEMA_VERSION,
    migration_registry_fingerprint,
)


def main() -> int:
    convergence = audit_observation_definitions(ROOT)
    payload = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "registry_fingerprint": migration_registry_fingerprint(),
        "convergence_fingerprint": convergence.fingerprint,
        "entries": [
            entry.to_canonical_data() for entry in MIGRATION_ENTRIES
        ],
        "forbidden_definitions": list(
            convergence.forbidden_duplicates
        ),
    }
    payload["report_fingerprint"] = sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    output = ROOT / "docs" / "audits"
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "genesis_iv_b4_observation_migration.json"
    md_path = output / "genesis_iv_b4_observation_migration.md"

    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Genesis IV-B4 Observation Migration Report",
        "",
        f"**Registry fingerprint:** `{payload['registry_fingerprint']}`  ",
        f"**Convergence fingerprint:** `{payload['convergence_fingerprint']}`  ",
        f"**Report fingerprint:** `{payload['report_fingerprint']}`",
        "",
        "## Governed Definitions",
        "",
    ]
    for entry in MIGRATION_ENTRIES:
        lines.extend(
            [
                f"### `{entry.path}`",
                "",
                f"- Semantic role: `{entry.semantic_role}`",
                f"- Disposition: `{entry.disposition.value}`",
                f"- Readiness: `{entry.readiness.value}`",
                (
                    f"- Target name: `{entry.target_name}`"
                    if entry.target_name
                    else "- Target name: canonical migration"
                ),
                f"- Rationale: {entry.rationale}",
                "",
            ]
        )

    lines.extend(["## Forbidden Definitions", ""])
    if convergence.forbidden_duplicates:
        lines.extend(
            f"- `{path}`"
            for path in convergence.forbidden_duplicates
        )
    else:
        lines.append("- None")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[PASS] JSON report     : {json_path}")
    print(f"[PASS] Markdown report : {md_path}")
    print(
        "[PASS] Migration report fingerprint: "
        f"{payload['report_fingerprint']}"
    )
    return 1 if convergence.forbidden_duplicates else 0


if __name__ == "__main__":
    raise SystemExit(main())

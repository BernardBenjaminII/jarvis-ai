from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.audit import RepositoryInventoryBuilder
from core.governance.constitution.extraction import (
    CONSTITUTIONAL_EXTRACTION_SCHEMA_VERSION,
    ConstitutionalExtractionEngine,
)


def main() -> int:
    output = PROJECT_ROOT / "artifacts/audit/km0000-c1"
    inventory = RepositoryInventoryBuilder().build(PROJECT_ROOT)
    engine = ConstitutionalExtractionEngine()
    first = engine.extract(root=PROJECT_ROOT, inventory=inventory, output_directory=output)
    second = engine.extract(root=PROJECT_ROOT, inventory=inventory)

    checks: list[tuple[str, bool, str]] = []
    checks.append(("Certified C0 inventory available", bool(inventory.fingerprint), inventory.fingerprint))
    checks.append(("Extraction schema is supported", first.schema_version == CONSTITUTIONAL_EXTRACTION_SCHEMA_VERSION, first.schema_version))
    checks.append(("Constitutional sources discovered", len(first.sources) > 0, f"count={len(first.sources)}"))
    checks.append(("Repository constitutional extraction completed", first.statistics.claims == len(first.claims), f"claims={len(first.claims)}"))
    checks.append(("Claims use deterministic path and line ordering", list(first.claims) == sorted(first.claims, key=lambda x: (x.locator.path, x.locator.start_line, x.claim_id)), f"count={len(first.claims)}"))
    checks.append(("Claim identifiers are unique", len({x.claim_id for x in first.claims}) == len(first.claims), f"count={len(first.claims)}"))
    checks.append(("Every claim retains repository evidence", all(x.source_repository_id and x.locator.path and x.locator.excerpt_sha256 for x in first.claims), "repository id, locator, excerpt hash"))
    checks.append(("Extraction is deterministic", first.fingerprint == second.fingerprint, first.fingerprint))
    checks.append(("Extraction binds to repository fingerprint", first.repository_fingerprint == inventory.fingerprint, inventory.fingerprint))

    expected = {
        "constitutional_extraction.json", "constitutional_claims.json",
        "constitutional_sources.json", "constitutional_extraction_report.md",
    }
    present = {item.name for item in output.iterdir()} if output.exists() else set()
    checks.append(("Canonical extraction artifact set", expected <= present, f"missing={len(expected - present)}"))
    json_files = [output / name for name in expected if name.endswith(".json")]
    json_valid = True
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            json_valid = False
    checks.append(("Extraction JSON artifacts are valid", json_valid, f"files={len(json_files)}"))

    failures = 0
    for label, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {label} — {detail}")
        failures += not passed

    print("------------------------------------------------------------------------")
    print(f"Repository fingerprint : {inventory.fingerprint}")
    print(f"Extraction fingerprint : {first.fingerprint}")
    print(f"Source documents       : {first.statistics.source_documents}")
    print(f"Constitutional claims  : {first.statistics.claims}")
    print(f"Normative claims       : {first.statistics.normative_claims}")
    print(f"Diagnostics            : {first.statistics.diagnostics}")
    print("------------------------------------------------------------------------")
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("========================================================================")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Certification verifier for Genesis IV-B3 convergence governance."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = (
    "core/observation/__init__.py",
    "core/observation/adapters.py",
    "core/observation/audit.py",
    "core/observation/contracts.py",
    "core/observation/enums.py",
    "core/observation/errors.py",
    "core/observation/serialization.py",
    "dev/report_genesis_iv_b3_convergence.py",
    "dev/verification/verify_genesis_iv_b3.py",
    "dev/verify_genesis_4b3.sh",
    "tests/test_genesis_iv_b3_canonical_observation_convergence.py",
    "tests/test_genesis_iv_b3_convergence_governance.py",
    "docs/architecture/convergence/"
    "genesis_iv_b3_canonical_observation_convergence.md",
    "docs/decisions/"
    "ADR-0038-canonical-observation-convergence.md",
    "standards/executive/OCS-0000.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical IV-B3 governance file set",
    )

    observation = importlib.import_module("core.observation")
    required_public = (
        "Observation",
        "ObservationSource",
        "ObservationContext",
        "ObservationDomain",
        "ObservationKind",
        "RealityClass",
        "SourceType",
        "adapt_legacy_observation",
        "audit_observation_definitions",
        "canonical_json",
    )
    check(
        all(
            hasattr(observation, name)
            for name in required_public
        ),
        "Stable canonical public imports",
    )

    timestamp = datetime(
        2026,
        7,
        26,
        8,
        0,
        tzinfo=timezone.utc,
    )
    source = observation.ObservationSource.create(
        reality_class=observation.RealityClass.RECORDED,
        source_type=observation.SourceType.BOOK,
        identifier="book:iv-b3-certification",
        producer="academy-reader",
        collector="document-extractor",
        authority=observation.SourceAuthority.PRIMARY,
        segment_id="chapter-1",
    )
    first = observation.Observation.create(
        domain=observation.ObservationDomain.KNOWLEDGE,
        observation_type="knowledge.claim",
        kind=observation.ObservationKind.CONTENT,
        subject="genesis-iv-b3",
        predicate="establishes",
        value="Canonical observation convergence governance.",
        source=source,
        observed_at=timestamp,
        recorded_at=timestamp,
        confidence=0.99,
    )
    second = observation.Observation.create(
        domain=observation.ObservationDomain.KNOWLEDGE,
        observation_type="knowledge.claim",
        kind=observation.ObservationKind.CONTENT,
        subject="genesis-iv-b3",
        predicate="establishes",
        value="Canonical observation convergence governance.",
        source=source,
        observed_at=timestamp,
        recorded_at=timestamp,
        confidence=0.99,
    )

    check(
        first.observation_id == second.observation_id,
        "Deterministic observation identity",
    )
    check(
        first.source.reality_class
        is observation.RealityClass.RECORDED,
        "Recorded-reality observation support",
    )
    check(
        first.source.source_type
        is observation.SourceType.BOOK,
        "Books and files are first-class sources",
    )

    audit = importlib.import_module("core.observation.audit")
    report = audit.audit_observation_definitions(ROOT)

    print()
    print(
        audit.format_observation_convergence_report(
            report
        )
    )
    print()

    check(
        report.canonical_definitions
        == (audit.CANONICAL_OBSERVATION_PATH,),
        "Exactly one canonical Observation owner",
    )
    check(
        not report.forbidden_duplicates,
        "No ungoverned Observation definitions",
    )
    check(
        report.converged,
        "Observation convergence governance gate",
    )

    output_directory = ROOT / "docs" / "audits"
    json_path, markdown_path = (
        audit.write_observation_convergence_reports(
            report,
            output_directory,
        )
    )
    check(
        json_path.is_file() and markdown_path.is_file(),
        "Deterministic convergence reports generated",
    )

    architecture_path = (
        ROOT
        / "docs/architecture/convergence/"
        "genesis_iv_b3_canonical_observation_convergence.md"
    )
    architecture = architecture_path.read_text(
        encoding="utf-8"
    )
    check(
        "Recorded Reality" in architecture
        and "books" in architecture.lower()
        and "files" in architecture.lower(),
        "Knowledge-document observation doctrine",
    )

    certification_payload = {
        "schema": observation.SCHEMA_VERSION,
        "observation": first.to_canonical_data(),
        "convergence": report.to_canonical_data(),
    }
    fingerprint = sha256(
        json.dumps(
            certification_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    print(
        "[PASS] Deterministic IV-B3 certification fingerprint: "
        f"{fingerprint}"
    )


if __name__ == "__main__":
    main()

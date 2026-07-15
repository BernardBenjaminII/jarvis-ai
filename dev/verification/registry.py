"""
Canonical registry of JARVIS Gen 2 verification suites.

Ordering is intentional and follows architectural dependency order.
"""

from __future__ import annotations

from dev.verification.models import (
    SuiteDefinition,
)


VERIFICATION_SUITES: tuple[SuiteDefinition, ...] = (
    SuiteDefinition(
        suite_id="6b",
        name="Phase VI-B Document Safety",
        script_path="dev/verify_phase_6b.sh",
        category="assimilation",
        description=(
            "Failure-safe document processing, retries, "
            "attempts, and state transitions."
        ),
    ),
    SuiteDefinition(
        suite_id="6c",
        name="Phase VI-C Persistent Missions",
        script_path="dev/verify_phase_6c.sh",
        category="missions",
        description=(
            "Durable mission reconstruction, checkpointing, "
            "resume, and completion."
        ),
    ),
    SuiteDefinition(
        suite_id="6d0",
        name="Phase VI-D0 Handler Lifecycle",
        script_path="dev/verify_phase_6d0.sh",
        category="handlers",
        description="Canonical assimilation handler lifecycle.",
    ),
    SuiteDefinition(
        suite_id="6d1",
        name="Phase VI-D1 Handler Registry",
        script_path="dev/verify_phase_6d1.sh",
        category="handlers",
        description="Handler registration and object-type lookup.",
    ),
    SuiteDefinition(
        suite_id="6d2",
        name="Phase VI-D2 Collection Planning",
        script_path="dev/verify_phase_6d2.sh",
        category="handlers",
        description=(
            "Deterministic source-collection expansion planning."
        ),
    ),
    SuiteDefinition(
        suite_id="6e1",
        name="Phase VI-E1 State Service",
        script_path="dev/verify_phase_6e1.sh",
        category="services",
        description="Registry and queue state-transition service.",
    ),
    SuiteDefinition(
        suite_id="6e2",
        name="Phase VI-E2 Persistence Service",
        script_path="dev/verify_phase_6e2.sh",
        category="services",
        description="Document-text and chunk persistence.",
    ),
    SuiteDefinition(
        suite_id="6e3",
        name="Phase VI-E3 Attempt Journal",
        script_path="dev/verify_phase_6e3.sh",
        category="services",
        description="Durable attempt creation and diagnostics.",
    ),
    SuiteDefinition(
        suite_id="6e4",
        name="Phase VI-E4 Extraction Service",
        script_path="dev/verify_phase_6e4.sh",
        category="services",
        description=(
            "Format-aware extraction, checksums, and chunking."
        ),
    ),
    SuiteDefinition(
        suite_id="6f2",
        name="Phase VI-F2 Architecture Contracts",
        script_path="dev/verify_phase_6f2.sh",
        category="contracts",
        description=(
            "API, repository, dependency, and ownership "
            "contracts."
        ),
    ),
    SuiteDefinition(
        suite_id="6f3",
        name="Phase VI-F3 Runner Composition",
        script_path="dev/verify_phase_6f3.sh",
        category="contracts",
        description=(
            "Runner constructor, dependency injection, and "
            "composition contracts."
        ),
    ),
    SuiteDefinition(
        suite_id="6f4",
        name="Phase VI-F4 Determinism and Performance",
        script_path="dev/verify_phase_6f4.sh",
        category="performance",
        description=(
            "Determinism, bounded execution, and temporary "
            "performance baselines."
        ),
    ),
    SuiteDefinition(
        suite_id="6f5",
        name="Phase VI-F5 Verification Framework",
        script_path="dev/verify_phase_6f5.sh",
        category="verification",
        description=(
            "Verification registry, reporting, filtering, and "
            "framework contracts."
        ),
    ),
    SuiteDefinition(
        suite_id="6f7",
        name="Phase VI-F7 Developer Infrastructure",
        script_path="dev/verify_phase_6f7.sh",
        category="developer-infrastructure",
        description=(
            "Safe-commit workflow, CI verification, and "
            "developer release gates."
        ),
    ),
    SuiteDefinition(
        suite_id="7a1",
        name="Phase VII-A1 Acquisition Foundation",
        script_path="dev/verify_phase_7a1.sh",
        category="acquisition",
        description=(
            "Immutable acquisition models, provider registry, "
            "filesystem discovery, and deterministic planning."
        ),
    ),

    SuiteDefinition(
        suite_id="7a2",
        name="Phase VII-A2 Admission Engine",
        script_path="dev/verify_phase_7a2.sh",
        category="acquisition",
        description=(
            "Deterministic admission policies, ordered "
            "evaluation, and admission decisions."
        ),
    ),
    SuiteDefinition(
        suite_id="7a3",
        name="Phase VII-A3 Provenance Persistence",
        script_path="dev/verify_phase_7a3.sh",
        category="acquisition",
        description=(
            "Durable source identity, sightings, checksum "
            "inventory, and admission-decision history."
        ),
    ),
    SuiteDefinition(
        suite_id="7a4",
        name="Phase VII-A4 Durable Admission Workflow",
        script_path="dev/verify_phase_7a4.sh",
        category="acquisition",
        description=(
            "Provenance-backed duplicate lookup, admission "
            "evaluation, and durable decision recording."
        ),
    ),


    SuiteDefinition(
        suite_id="7a5",
        name="Phase VII-A5 Acquisition Missions",
        script_path="dev/verify_phase_7a5.sh",
        category="acquisition",
        description=(
            "Durable mission construction and complete "
            "candidate-outcome accounting."
        ),
    ),

)


def validate_registry(
    suites: tuple[SuiteDefinition, ...] = VERIFICATION_SUITES,
) -> None:
    """Validate canonical registry uniqueness."""

    suite_ids = [
        suite.suite_id
        for suite in suites
    ]

    names = [
        suite.name
        for suite in suites
    ]

    paths = [
        suite.script_path
        for suite in suites
    ]

    if len(suite_ids) != len(set(suite_ids)):
        raise ValueError(
            "Verification suite IDs must be unique"
        )

    if len(names) != len(set(names)):
        raise ValueError(
            "Verification suite names must be unique"
        )

    if len(paths) != len(set(paths)):
        raise ValueError(
            "Verification suite script paths must be unique"
        )

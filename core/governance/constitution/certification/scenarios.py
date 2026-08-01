from __future__ import annotations

from .contracts import ScenarioKind
from .fingerprints import canonical_fingerprint
from .identifiers import stable_identifier
from .models import CertificationScenario


def build_foundational_scenarios() -> tuple[CertificationScenario, ...]:
    definitions = (
        (
            ScenarioKind.POSITIVE_COMPLIANCE.value,
            "Positive compliance",
            "Prove that a live constitutional article can produce a compliant result.",
            "compliant",
        ),
        (
            ScenarioKind.NEGATIVE_COMPLIANCE.value,
            "Negative compliance",
            "Prove that a deterministic contradiction can produce a noncompliant result.",
            "noncompliant",
        ),
        (
            ScenarioKind.REVIEW_REQUIRED.value,
            "Review required",
            "Prove that an ambiguous but applicable subject can require human review.",
            "review_required",
        ),
        (
            ScenarioKind.NOT_APPLICABLE.value,
            "Not applicable",
            "Prove that an unrelated subject remains outside constitutional applicability.",
            "not_applicable",
        ),
        (
            ScenarioKind.COVERAGE.value,
            "Coverage",
            "Prove that every certification subject is represented by an assessment.",
            "pass",
        ),
        (
            ScenarioKind.RANKING.value,
            "Ranking",
            "Prove that the expected constitutional article ranks first.",
            "pass",
        ),
        (
            ScenarioKind.TRACEABILITY.value,
            "Traceability",
            "Prove the chain from subject to article and upstream fingerprints.",
            "pass",
        ),
        (
            ScenarioKind.DETERMINISM.value,
            "Determinism",
            "Prove that repeated certification produces the same fingerprint.",
            "pass",
        ),
    )

    scenarios = []
    for kind, title, description, expected_status in definitions:
        basis = {
            "kind": kind,
            "title": title,
            "description": description,
            "expected_status": expected_status,
            "expected_article_id": "",
        }
        fingerprint = canonical_fingerprint(basis)
        scenarios.append(
            CertificationScenario(
                scenario_id=stable_identifier("CSC", fingerprint),
                kind=kind,
                title=title,
                description=description,
                expected_status=expected_status,
                expected_article_id="",
                fingerprint=fingerprint,
            )
        )

    return tuple(sorted(scenarios, key=lambda item: item.scenario_id))

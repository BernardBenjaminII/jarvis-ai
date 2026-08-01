from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .contracts import CERTIFICATION_SCHEMA_VERSION, CertificationStatus
from .executor import LiveCertificationExecutor
from .fingerprints import canonical_fingerprint
from .models import (
    CertificationAssessment,
    CertificationPolicy,
    CertificationStatistics,
    ScenarioResult,
)
from .scenarios import build_foundational_scenarios


class ConstitutionalCertificationEngine:
    def assess_framework(
        self,
        *,
        repository_fingerprint: str,
        extraction_fingerprint: str,
        analysis_fingerprint: str,
        ratification_fingerprint: str,
        compliance_fingerprint: str,
        policy: CertificationPolicy | None = None,
    ) -> CertificationAssessment:
        active_policy = policy or CertificationPolicy()
        scenarios = build_foundational_scenarios()

        results = []
        for scenario in scenarios:
            basis = {
                "scenario_id": scenario.scenario_id,
                "status": CertificationStatus.SKIPPED.value,
                "observed_status": "not_executed",
                "observed_article_id": "",
                "rank": 0,
                "findings": 0,
                "traceability_complete": False,
                "rationale": "Framework scenario registered; executable scenario logic is provided by Pack 2.",
            }
            results.append(
                ScenarioResult(
                    scenario_id=scenario.scenario_id,
                    status=CertificationStatus.SKIPPED.value,
                    observed_status="not_executed",
                    observed_article_id="",
                    rank=0,
                    findings=0,
                    traceability_complete=False,
                    rationale=basis["rationale"],
                    fingerprint=canonical_fingerprint(basis),
                )
            )

        results.sort(key=lambda item: item.scenario_id)
        counts = defaultdict(int)
        for result in results:
            counts[result.status] += 1

        statistics = CertificationStatistics(
            scenarios=len(scenarios),
            passed=counts[CertificationStatus.PASS.value],
            failed=counts[CertificationStatus.FAIL.value],
            skipped=counts[CertificationStatus.SKIPPED.value],
            positive_findings=0,
            negative_findings=0,
            review_findings=0,
            not_applicable_subjects=0,
            diagnostics=0,
        )

        basis = {
            "schema_version": CERTIFICATION_SCHEMA_VERSION,
            "repository_fingerprint": repository_fingerprint,
            "extraction_fingerprint": extraction_fingerprint,
            "analysis_fingerprint": analysis_fingerprint,
            "ratification_fingerprint": ratification_fingerprint,
            "compliance_fingerprint": compliance_fingerprint,
            "policy": active_policy.to_dict(),
            "scenarios": [item.to_dict() for item in scenarios],
            "results": [item.to_dict() for item in results],
            "statistics": statistics.to_dict(),
        }

        return CertificationAssessment(
            schema_version=CERTIFICATION_SCHEMA_VERSION,
            repository_fingerprint=repository_fingerprint,
            extraction_fingerprint=extraction_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            ratification_fingerprint=ratification_fingerprint,
            compliance_fingerprint=compliance_fingerprint,
            certification_fingerprint=canonical_fingerprint(basis),
            policy=active_policy,
            scenarios=scenarios,
            results=tuple(results),
            statistics=statistics,
            diagnostics=(),
        )

    def assess_live_scenarios(
        self,
        *,
        ratification_directory: Path,
        compliance_fingerprint: str,
        policy: CertificationPolicy | None = None,
    ) -> CertificationAssessment:
        return LiveCertificationExecutor().execute(
            ratification_directory=ratification_directory,
            compliance_fingerprint=compliance_fingerprint,
            policy=policy,
        )

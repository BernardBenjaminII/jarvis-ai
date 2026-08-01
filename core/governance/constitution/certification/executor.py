from __future__ import annotations

import json
import tempfile
from collections import defaultdict
from pathlib import Path

from core.governance.constitution.compliance import (
    CompliancePolicy,
    ConstitutionalComplianceEngine,
)
from core.governance.constitution.compliance.loader import load_ratification

from .contracts import CERTIFICATION_SCHEMA_VERSION, CertificationStatus
from .fingerprints import canonical_fingerprint
from .live_scenarios import build_live_certification_scenarios
from .models import (
    CertificationAssessment,
    CertificationPolicy,
    CertificationStatistics,
    LiveCertificationScenario,
    ScenarioResult,
)


class LiveCertificationExecutor:
    def execute(
        self,
        *,
        ratification_directory: Path,
        compliance_fingerprint: str,
        policy: CertificationPolicy | None = None,
    ) -> CertificationAssessment:
        active_policy = policy or CertificationPolicy()
        (
            repository_fingerprint,
            extraction_fingerprint,
            analysis_fingerprint,
            ratification_fingerprint,
            articles,
        ) = load_ratification(
            ratification_directory,
            require_ratified_only=True,
        )
        scenarios = build_live_certification_scenarios(articles)

        results: list[ScenarioResult] = []
        for scenario in scenarios:
            results.append(
                self._execute_scenario(
                    ratification_directory=ratification_directory,
                    scenario=scenario,
                )
            )

        results.sort(key=lambda item: item.scenario_id)
        diagnostics = self._policy_diagnostics(active_policy, scenarios, results)

        status_counts = defaultdict(int)
        for result in results:
            status_counts[result.status] += 1

        result_by_id = {item.scenario_id: item for item in results}
        positive_findings = self._finding_count(
            scenarios, result_by_id, "positive_compliance"
        )
        negative_findings = self._finding_count(
            scenarios, result_by_id, "negative_compliance"
        )
        review_findings = self._finding_count(
            scenarios, result_by_id, "review_required"
        )
        not_applicable_subjects = sum(
            1
            for scenario in scenarios
            if scenario.kind == "not_applicable"
            and result_by_id[scenario.scenario_id].observed_status == "not_applicable"
        )

        statistics = CertificationStatistics(
            scenarios=len(scenarios),
            passed=status_counts[CertificationStatus.PASS.value],
            failed=status_counts[CertificationStatus.FAIL.value],
            skipped=status_counts[CertificationStatus.SKIPPED.value],
            positive_findings=positive_findings,
            negative_findings=negative_findings,
            review_findings=review_findings,
            not_applicable_subjects=not_applicable_subjects,
            diagnostics=len(diagnostics),
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
            "diagnostics": list(diagnostics),
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
            diagnostics=tuple(diagnostics),
        )

    def _execute_scenario(
        self,
        *,
        ratification_directory: Path,
        scenario: LiveCertificationScenario,
    ) -> ScenarioResult:
        subject_payload = {
            "subjects": [
                {
                    "subject_id": scenario.subject_id,
                    "subject_type": "constitutional_certification_fixture",
                    "path": f"certification://{scenario.scenario_id}",
                    "title": scenario.subject_title,
                    "content": scenario.subject_content,
                    "domain": scenario.subject_domain,
                }
            ]
        }

        with tempfile.TemporaryDirectory(prefix="jarvis-c4-1-pack2-") as temporary:
            subject_path = Path(temporary) / "subjects.json"
            subject_path.write_text(
                json.dumps(subject_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            assessment = ConstitutionalComplianceEngine().assess(
                ratification_directory=ratification_directory,
                subject_path=subject_path,
                policy=CompliancePolicy(
                    minimum_match_score=0.35,
                    contradiction_threshold=0.72,
                    require_ratified_articles_only=True,
                    fail_on_unresolved_article=False,
                ),
            )

        subject_assessment = next(
            item
            for item in assessment.assessments
            if item.subject_id == scenario.subject_id
        )
        target_findings = [
            item
            for item in assessment.findings
            if item.subject_id == scenario.subject_id
            and (
                not scenario.expected_article_id
                or item.article_id == scenario.expected_article_id
            )
        ]

        ranked = sorted(
            (
                item
                for item in assessment.findings
                if item.subject_id == scenario.subject_id
            ),
            key=lambda item: (-item.score, item.article_id, item.finding_id),
        )
        observed_article_id = ranked[0].article_id if ranked else ""
        rank = 0
        if scenario.expected_article_id:
            for index, finding in enumerate(ranked, start=1):
                if finding.article_id == scenario.expected_article_id:
                    rank = index
                    break

        if scenario.expected_status == "not_applicable":
            observed_status = subject_assessment.overall_status
            passed = observed_status == scenario.expected_status and not ranked
            findings = len(ranked)
        else:
            expected_finding = next(
                (
                    item
                    for item in target_findings
                    if item.status == scenario.expected_status
                ),
                None,
            )
            observed_status = (
                expected_finding.status
                if expected_finding is not None
                else (
                    target_findings[0].status
                    if target_findings
                    else subject_assessment.overall_status
                )
            )
            passed = expected_finding is not None
            findings = len(target_findings)

        traceability_complete = bool(
            assessment.repository_fingerprint
            and assessment.extraction_fingerprint
            and assessment.analysis_fingerprint
            and assessment.ratification_fingerprint
            and (
                scenario.expected_status == "not_applicable"
                or (
                    scenario.expected_article_id
                    and scenario.source_article_fingerprint
                )
            )
        )

        if passed:
            rationale = (
                f"Observed expected status '{scenario.expected_status}' "
                f"for live scenario '{scenario.kind}'."
            )
        else:
            rationale = (
                f"Expected '{scenario.expected_status}' but observed "
                f"'{observed_status}' for live scenario '{scenario.kind}'."
            )

        result_basis = {
            "scenario_id": scenario.scenario_id,
            "status": (
                CertificationStatus.PASS.value
                if passed
                else CertificationStatus.FAIL.value
            ),
            "observed_status": observed_status,
            "observed_article_id": observed_article_id,
            "rank": rank,
            "findings": findings,
            "traceability_complete": traceability_complete,
            "rationale": rationale,
        }

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            status=result_basis["status"],
            observed_status=observed_status,
            observed_article_id=observed_article_id,
            rank=rank,
            findings=findings,
            traceability_complete=traceability_complete,
            rationale=rationale,
            fingerprint=canonical_fingerprint(result_basis),
        )

    @staticmethod
    def _finding_count(
        scenarios: tuple[LiveCertificationScenario, ...],
        results: dict[str, ScenarioResult],
        kind: str,
    ) -> int:
        return sum(
            results[scenario.scenario_id].findings
            for scenario in scenarios
            if scenario.kind == kind
            and results[scenario.scenario_id].status == CertificationStatus.PASS.value
        )

    @staticmethod
    def _policy_diagnostics(
        policy: CertificationPolicy,
        scenarios: tuple[LiveCertificationScenario, ...],
        results: list[ScenarioResult],
    ) -> list[str]:
        by_id = {item.scenario_id: item for item in results}
        by_kind = {
            scenario.kind: by_id[scenario.scenario_id]
            for scenario in scenarios
        }
        diagnostics: list[str] = []

        required_kinds = (
            "positive_compliance",
            "negative_compliance",
            "review_required",
            "not_applicable",
        )
        for kind in required_kinds:
            result = by_kind.get(kind)
            if result is None:
                diagnostics.append(f"Missing required live scenario: {kind}")
            elif result.status != CertificationStatus.PASS.value:
                diagnostics.append(f"Live scenario failed: {kind}")

        applicable = [
            (scenario, by_id[scenario.scenario_id])
            for scenario in scenarios
            if scenario.expected_article_id
        ]
        if policy.require_rank_one_match:
            for scenario, result in applicable:
                if result.rank != 1:
                    diagnostics.append(
                        f"Expected article did not rank first for {scenario.kind}: "
                        f"rank={result.rank}"
                    )

        if policy.require_complete_traceability:
            for result in results:
                if not result.traceability_complete:
                    diagnostics.append(
                        f"Traceability incomplete for scenario {result.scenario_id}"
                    )

        return diagnostics

from __future__ import annotations

import inspect
import unittest

from core.government import (
    AssessmentState,
    AssignmentRequest,
    AuthorityLevel,
    ConstitutionalIdentifier,
    ConstitutionalObjectKind,
    Department,
    DepartmentAssessment,
    DepartmentReport,
    DirectiveRequest,
    ExecutiveGovernmentSnapshot,
    ExecutiveGovernmentView,
    ExecutiveIntegrationProvider,
    ExecutiveRecommendation,
    GovernmentSnapshot,
    HealthState,
    LifecycleState,
    OrganizationalAssessment,
    OrganizationalGraph,
    OrganizationalRelationship,
    ReadinessState,
    RecommendationPriority,
    RelationshipKind,
)


class ExecutiveIntegrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executive = ConstitutionalIdentifier(
            ConstitutionalObjectKind.EXECUTIVE,
            "government",
            "executive",
        )
        self.knowledge = ConstitutionalIdentifier(
            ConstitutionalObjectKind.DIRECTORATE,
            "government",
            "knowledge",
        )
        self.assimilation = ConstitutionalIdentifier(
            ConstitutionalObjectKind.DEPARTMENT,
            "knowledge",
            "assimilation",
        )
        self.department = Department(
            identifier=self.assimilation,
            title="Assimilation Department",
            mission="Transform admitted sources into governed knowledge.",
            authority=AuthorityLevel.DEPARTMENT,
            lifecycle=LifecycleState.ACTIVE,
            health=HealthState.HEALTHY,
            readiness=ReadinessState.READY,
            owner=self.knowledge,
        )
        self.relationship = OrganizationalRelationship(
            self.knowledge,
            RelationshipKind.OWNS,
            self.assimilation,
        )
        self.snapshot = GovernmentSnapshot(
            snapshot_id="government-1",
            objects=(self.department,),
            relationships=(self.relationship,),
        )

    def test_integration_provider_is_abstract(self) -> None:
        self.assertTrue(inspect.isabstract(ExecutiveIntegrationProvider))

    def test_assessment_is_deterministic(self) -> None:
        department = DepartmentAssessment(
            department=self.assimilation,
            state=AssessmentState.NOMINAL,
            health=HealthState.HEALTHY,
            readiness=ReadinessState.READY,
            summary="Department is operational.",
            risks=("None", "None"),
        )
        first = OrganizationalAssessment(
            state=AssessmentState.NOMINAL,
            summary="Organization is operational.",
            departments=(department,),
        )
        second = OrganizationalAssessment(
            state=AssessmentState.NOMINAL,
            summary="Organization is operational.",
            departments=(department,),
        )
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_directive_requires_constitutional_basis(self) -> None:
        with self.assertRaises(ValueError):
            DirectiveRequest(
                directive_id="directive-1",
                issuing_authority=self.executive,
                responsible_organization=self.knowledge,
                purpose="Improve readiness.",
                required_action="Run verification.",
                expected_outcome="Certified readiness.",
                constitutional_basis=(),
            )

    def test_assignment_rejects_self_assignment(self) -> None:
        with self.assertRaises(ValueError):
            AssignmentRequest(
                assignment_id="assignment-1",
                subject=self.knowledge,
                assignee=self.knowledge,
                objective="Coordinate itself.",
            )

    def test_government_view_validates_graph(self) -> None:
        assessment = OrganizationalAssessment(
            state=AssessmentState.NOMINAL,
            summary="Organization is operational.",
        )
        graph = OrganizationalGraph.create((self.relationship,))
        view = ExecutiveGovernmentView(
            government=self.snapshot,
            graph=graph,
            assessment=assessment,
        )
        self.assertEqual(view.graph, graph)

    def test_view_rejects_mismatched_graph(self) -> None:
        assessment = OrganizationalAssessment(
            state=AssessmentState.NOMINAL,
            summary="Organization is operational.",
        )
        with self.assertRaises(ValueError):
            ExecutiveGovernmentView(
                government=self.snapshot,
                graph=OrganizationalGraph.create(()),
                assessment=assessment,
            )

    def test_view_and_snapshot_fingerprints_are_stable(self) -> None:
        assessment = OrganizationalAssessment(
            state=AssessmentState.NOMINAL,
            summary="Organization is operational.",
        )
        report = DepartmentReport(
            department=self.assimilation,
            health=HealthState.HEALTHY,
            readiness=ReadinessState.READY,
            summary="Operational.",
            metrics={"processed": "10"},
        )
        recommendation = ExecutiveRecommendation(
            recommendation_id="recommendation-1",
            title="Continue operations",
            rationale="All indicators are nominal.",
            priority=RecommendationPriority.ROUTINE,
            responsible_organization=self.knowledge,
        )
        graph = OrganizationalGraph.create((self.relationship,))
        first = ExecutiveGovernmentView(
            government=self.snapshot,
            graph=graph,
            assessment=assessment,
            reports=(report,),
            recommendations=(recommendation,),
        )
        second = ExecutiveGovernmentView(
            government=self.snapshot,
            graph=graph,
            assessment=assessment,
            reports=(report,),
            recommendations=(recommendation,),
        )
        self.assertEqual(first.fingerprint, second.fingerprint)

        snapshot = ExecutiveGovernmentSnapshot(
            snapshot_id="executive-1",
            view=first,
        )
        self.assertEqual(snapshot.fingerprint, snapshot.fingerprint)


if __name__ == "__main__":
    unittest.main()

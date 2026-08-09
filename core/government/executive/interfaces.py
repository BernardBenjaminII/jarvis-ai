"""Abstract Executive integration interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.government.models import ConstitutionalIdentifier
from core.government.registry import GovernmentRegistry

from .contracts import (
    AssignmentRequest,
    DepartmentReport,
    DirectiveRequest,
    ExecutiveGovernmentSnapshot,
    ExecutiveGovernmentView,
    ExecutiveRecommendation,
    OrganizationalAssessment,
)


class ExecutiveGovernmentProvider(ABC):
    @abstractmethod
    def current_view(self) -> ExecutiveGovernmentView:
        raise NotImplementedError

    @abstractmethod
    def snapshot(self, snapshot_id: str) -> ExecutiveGovernmentSnapshot:
        raise NotImplementedError


class OrganizationalSupervisor(ABC):
    @abstractmethod
    def assess(self) -> OrganizationalAssessment:
        raise NotImplementedError

    @abstractmethod
    def assess_department(
        self,
        department: ConstitutionalIdentifier,
    ) -> DepartmentReport:
        raise NotImplementedError


class GovernmentAssessmentProvider(ABC):
    @abstractmethod
    def organizational_assessment(self) -> OrganizationalAssessment:
        raise NotImplementedError


class ExecutiveRecommendationProvider(ABC):
    @abstractmethod
    def recommendations(self) -> tuple[ExecutiveRecommendation, ...]:
        raise NotImplementedError


class DirectiveProvider(ABC):
    @abstractmethod
    def authorize(self, request: DirectiveRequest) -> DirectiveRequest:
        raise NotImplementedError

    @abstractmethod
    def issue(self, request: DirectiveRequest) -> DirectiveRequest:
        raise NotImplementedError


class AssignmentProvider(ABC):
    @abstractmethod
    def assign(self, request: AssignmentRequest) -> AssignmentRequest:
        raise NotImplementedError


class DepartmentReportProvider(ABC):
    @abstractmethod
    def report(
        self,
        department: ConstitutionalIdentifier,
    ) -> DepartmentReport:
        raise NotImplementedError

    @abstractmethod
    def reports(self) -> tuple[DepartmentReport, ...]:
        raise NotImplementedError


class ExecutiveSnapshotProvider(ABC):
    @abstractmethod
    def create_snapshot(
        self,
        snapshot_id: str,
    ) -> ExecutiveGovernmentSnapshot:
        raise NotImplementedError

    @abstractmethod
    def latest_snapshot(self) -> ExecutiveGovernmentSnapshot | None:
        raise NotImplementedError


class ExecutiveIntegrationProvider(ABC):
    @abstractmethod
    def registry(self) -> GovernmentRegistry:
        raise NotImplementedError

    @abstractmethod
    def government(self) -> ExecutiveGovernmentProvider:
        raise NotImplementedError

    @abstractmethod
    def supervisor(self) -> OrganizationalSupervisor:
        raise NotImplementedError

    @abstractmethod
    def assessment_provider(self) -> GovernmentAssessmentProvider:
        raise NotImplementedError

    @abstractmethod
    def recommendation_provider(self) -> ExecutiveRecommendationProvider:
        raise NotImplementedError

    @abstractmethod
    def directive_provider(self) -> DirectiveProvider:
        raise NotImplementedError

    @abstractmethod
    def assignment_provider(self) -> AssignmentProvider:
        raise NotImplementedError

    @abstractmethod
    def report_provider(self) -> DepartmentReportProvider:
        raise NotImplementedError

    @abstractmethod
    def snapshot_provider(self) -> ExecutiveSnapshotProvider:
        raise NotImplementedError

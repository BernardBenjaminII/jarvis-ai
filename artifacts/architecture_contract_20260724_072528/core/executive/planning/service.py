"""Application service for immutable mission-plan lifecycle operations."""

from __future__ import annotations

from dataclasses import replace

from core.executive.planning.enums import PlanState
from core.executive.planning.errors import InvalidPlanTransitionError
from core.executive.planning.models import (
    Dependency,
    Mission,
    MissionPlan,
    PlanVersion,
    create_plan_version,
)
from core.executive.planning.repository import PlanRepository
from core.executive.planning.validation import PlanValidator, ValidationReport


_ALLOWED_TRANSITIONS: dict[PlanState, frozenset[PlanState]] = {
    PlanState.DRAFT: frozenset(
        {
            PlanState.CONTEXT_GATHERING,
            PlanState.CANDIDATE,
            PlanState.TERMINATED,
        }
    ),
    PlanState.CONTEXT_GATHERING: frozenset(
        {
            PlanState.AWAITING_INFORMATION,
            PlanState.CANDIDATE,
            PlanState.TERMINATED,
        }
    ),
    PlanState.AWAITING_INFORMATION: frozenset(
        {
            PlanState.CONTEXT_GATHERING,
            PlanState.TERMINATED,
        }
    ),
    PlanState.CANDIDATE: frozenset(
        {
            PlanState.UNDER_REVIEW,
            PlanState.TERMINATED,
        }
    ),
    PlanState.UNDER_REVIEW: frozenset(
        {
            PlanState.REVISION_REQUIRED,
            PlanState.AWAITING_APPROVAL,
            PlanState.TERMINATED,
        }
    ),
    PlanState.REVISION_REQUIRED: frozenset(
        {
            PlanState.CANDIDATE,
            PlanState.TERMINATED,
        }
    ),
    PlanState.AWAITING_APPROVAL: frozenset(
        {
            PlanState.APPROVED,
            PlanState.REVISION_REQUIRED,
            PlanState.TERMINATED,
        }
    ),
    PlanState.APPROVED: frozenset(
        {
            PlanState.SCHEDULED,
            PlanState.ACTIVE,
            PlanState.TERMINATED,
        }
    ),
    PlanState.SCHEDULED: frozenset(
        {
            PlanState.ACTIVE,
            PlanState.SUSPENDED,
            PlanState.TERMINATED,
        }
    ),
    PlanState.ACTIVE: frozenset(
        {
            PlanState.REPLANNING,
            PlanState.SUSPENDED,
            PlanState.COMPLETED,
            PlanState.FAILED,
            PlanState.TERMINATED,
        }
    ),
    PlanState.REPLANNING: frozenset(
        {
            PlanState.AWAITING_APPROVAL,
            PlanState.ACTIVE,
            PlanState.SUSPENDED,
            PlanState.TERMINATED,
        }
    ),
    PlanState.SUSPENDED: frozenset(
        {
            PlanState.ACTIVE,
            PlanState.REPLANNING,
            PlanState.TERMINATED,
        }
    ),
    PlanState.COMPLETED: frozenset({PlanState.ARCHIVED}),
    PlanState.FAILED: frozenset({PlanState.ARCHIVED}),
    PlanState.TERMINATED: frozenset({PlanState.ARCHIVED}),
    PlanState.ARCHIVED: frozenset(),
}


class PlanningService:
    """Creates, validates, versions, and transitions mission plans."""

    def __init__(
        self,
        repository: PlanRepository,
        *,
        validator: PlanValidator | None = None,
    ) -> None:
        self._repository = repository
        self._validator = validator or PlanValidator()

    def create_plan(
        self,
        *,
        mission: Mission,
        dependencies: tuple[Dependency, ...] = (),
        created_by: str = "planning_director",
    ) -> MissionPlan:
        version = create_plan_version(
            mission=mission,
            dependencies=dependencies,
            state=PlanState.DRAFT,
            created_by=created_by,
        )

        self._validator.validate_or_raise(version)
        return self._repository.create(version)

    def revise_plan(
        self,
        *,
        plan_id: str,
        mission: Mission,
        reason: str,
        dependencies: tuple[Dependency, ...] | None = None,
        created_by: str = "planning_director",
        target_state: PlanState = PlanState.CANDIDATE,
    ) -> MissionPlan:
        if not reason.strip():
            raise ValueError("Plan revision reason cannot be empty")

        current = self._repository.get(plan_id).current
        next_version = PlanVersion(
            plan_id=plan_id,
            version=current.version + 1,
            parent_version=current.version,
            mission=mission,
            dependencies=(
                current.dependencies
                if dependencies is None
                else dependencies
            ),
            state=target_state,
            created_by=created_by,
            revision_reason=reason,
        )

        self._validator.validate_or_raise(next_version)
        return self._repository.append_version(next_version)

    def transition(
        self,
        *,
        plan_id: str,
        target_state: PlanState,
        reason: str,
        created_by: str = "planning_director",
    ) -> MissionPlan:
        current = self._repository.get(plan_id).current
        allowed = _ALLOWED_TRANSITIONS[current.state]

        if target_state not in allowed:
            raise InvalidPlanTransitionError(
                f"Invalid plan transition: "
                f"{current.state.value} -> {target_state.value}"
            )

        transitioned = replace(
            current,
            version=current.version + 1,
            parent_version=current.version,
            state=target_state,
            created_by=created_by,
            revision_reason=reason,
            fingerprint="",
        )

        self._validator.validate_or_raise(transitioned)
        return self._repository.append_version(transitioned)

    def validate(self, plan_id: str) -> ValidationReport:
        current = self._repository.get(plan_id).current
        return self._validator.validate(current)

    def get_plan(self, plan_id: str) -> MissionPlan:
        return self._repository.get(plan_id)

    def get_version(self, plan_id: str, version: int) -> PlanVersion:
        return self._repository.get_version(plan_id, version)

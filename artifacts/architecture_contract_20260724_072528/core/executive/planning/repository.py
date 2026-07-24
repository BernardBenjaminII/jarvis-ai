"""Persistence boundaries for immutable mission-plan versions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from core.executive.planning.errors import (
    ImmutablePlanVersionError,
    PlanNotFoundError,
    PlanVersionConflictError,
)
from core.executive.planning.models import MissionPlan, PlanVersion


class PlanRepository(ABC):
    """Abstract repository for immutable plan history."""

    @abstractmethod
    def create(self, initial_version: PlanVersion) -> MissionPlan:
        """Create a new mission plan."""

    @abstractmethod
    def append_version(self, version: PlanVersion) -> MissionPlan:
        """Append an immutable version to an existing plan."""

    @abstractmethod
    def get(self, plan_id: str) -> MissionPlan:
        """Return a mission plan and its complete history."""

    @abstractmethod
    def get_version(self, plan_id: str, version: int) -> PlanVersion:
        """Return one immutable historical version."""

    @abstractmethod
    def exists(self, plan_id: str) -> bool:
        """Return whether a plan exists."""

    @abstractmethod
    def list_plans(self) -> tuple[MissionPlan, ...]:
        """Return all persisted plans."""


class InMemoryPlanRepository(PlanRepository):
    """Thread-safe reference repository for planning contracts and tests.

    Production persistent adapters may implement the same PlanRepository
    contract using SQLite or another durable store.
    """

    def __init__(self) -> None:
        self._plans: dict[str, MissionPlan] = {}
        self._lock = RLock()

    def create(self, initial_version: PlanVersion) -> MissionPlan:
        with self._lock:
            if initial_version.plan_id in self._plans:
                raise PlanVersionConflictError(
                    f"Plan already exists: {initial_version.plan_id}"
                )

            if initial_version.version != 1:
                raise PlanVersionConflictError(
                    "Initial plan version must be version 1"
                )

            plan = MissionPlan(
                plan_id=initial_version.plan_id,
                versions=(initial_version,),
            )
            self._plans[plan.plan_id] = plan
            return plan

    def append_version(self, version: PlanVersion) -> MissionPlan:
        with self._lock:
            current = self.get(version.plan_id)
            expected_version = current.current.version + 1

            if version.version != expected_version:
                raise PlanVersionConflictError(
                    f"Expected version {expected_version}, "
                    f"received {version.version}"
                )

            if version.parent_version != current.current.version:
                raise PlanVersionConflictError(
                    "New plan version must reference the current version "
                    "as parent"
                )

            historical = {
                item.version: item for item in current.versions
            }

            if version.version in historical:
                if historical[version.version].fingerprint != version.fingerprint:
                    raise ImmutablePlanVersionError(
                        "Cannot overwrite an immutable plan version"
                    )

                return current

            updated = MissionPlan(
                plan_id=current.plan_id,
                versions=current.versions + (version,),
            )
            self._plans[current.plan_id] = updated
            return updated

    def get(self, plan_id: str) -> MissionPlan:
        with self._lock:
            try:
                return self._plans[plan_id]
            except KeyError as exc:
                raise PlanNotFoundError(
                    f"Plan does not exist: {plan_id}"
                ) from exc

    def get_version(self, plan_id: str, version: int) -> PlanVersion:
        return self.get(plan_id).get_version(version)

    def exists(self, plan_id: str) -> bool:
        with self._lock:
            return plan_id in self._plans

    def list_plans(self) -> tuple[MissionPlan, ...]:
        with self._lock:
            return tuple(
                self._plans[plan_id]
                for plan_id in sorted(self._plans)
            )

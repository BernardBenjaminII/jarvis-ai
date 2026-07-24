"""Structural validation for canonical mission plans."""

from __future__ import annotations

from dataclasses import dataclass

from core.executive.planning.dependencies import build_dependency_graph
from core.executive.planning.enums import AuthorizationMode
from core.executive.planning.errors import (
    DuplicatePlanElementError,
    PlanningValidationError,
)
from core.executive.planning.models import Mission, PlanVersion


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Structured result of plan validation."""

    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def raise_for_errors(self) -> None:
        if not self.passed:
            raise PlanningValidationError(
                "Mission plan validation failed",
                violations=self.errors,
            )


class PlanValidator:
    """Validates hierarchy, references, authorization, and dependencies."""

    def validate(self, plan_version: PlanVersion) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []

        self._validate_hierarchy(plan_version.mission, errors)
        self._validate_authorization(plan_version.mission, errors, warnings)
        self._validate_dependencies(plan_version, errors)
        self._validate_risks(plan_version.mission, warnings)

        return ValidationReport(
            passed=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def validate_or_raise(self, plan_version: PlanVersion) -> ValidationReport:
        report = self.validate(plan_version)
        report.raise_for_errors()
        return report

    def _validate_hierarchy(
        self,
        mission: Mission,
        errors: list[str],
    ) -> None:
        identifiers: list[str] = [mission.mission_id]

        for objective in mission.objectives:
            identifiers.append(objective.objective_id)

            if objective.mission_id != mission.mission_id:
                errors.append(
                    f"objective_parent_mismatch:{objective.objective_id}"
                )

            for task in objective.tasks:
                identifiers.append(task.task_id)

                if task.objective_id != objective.objective_id:
                    errors.append(f"task_parent_mismatch:{task.task_id}")

                for activity in task.activities:
                    identifiers.append(activity.activity_id)

                    if activity.task_id != task.task_id:
                        errors.append(
                            f"activity_parent_mismatch:{activity.activity_id}"
                        )

                    for command in activity.commands:
                        identifiers.append(command.command_id)

                        if command.activity_id != activity.activity_id:
                            errors.append(
                                "command_parent_mismatch:"
                                f"{command.command_id}"
                            )

        duplicate_ids = sorted(
            identifier
            for identifier in set(identifiers)
            if identifiers.count(identifier) > 1
        )

        if duplicate_ids:
            raise DuplicatePlanElementError(
                "Duplicate plan element identifiers detected",
                violations=tuple(
                    f"duplicate_element_id:{identifier}"
                    for identifier in duplicate_ids
                ),
            )

        if not mission.objectives:
            errors.append("mission_has_no_objectives")

    def _validate_authorization(
        self,
        mission: Mission,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        for objective in mission.objectives:
            if not objective.tasks:
                warnings.append(
                    f"objective_has_no_tasks:{objective.objective_id}"
                )

            for task in objective.tasks:
                if task.authorization.mode == AuthorizationMode.PROHIBITED:
                    warnings.append(f"prohibited_task:{task.task_id}")

                if not task.activities:
                    warnings.append(f"task_has_no_activities:{task.task_id}")

                for activity in task.activities:
                    if (
                        activity.authorization.inherited_from_parent
                        and task.authorization.mode
                        == AuthorizationMode.PLANNING_ONLY
                    ):
                        errors.append(
                            "invalid_authorization_inheritance:"
                            f"{activity.activity_id}"
                        )

                    for command in activity.commands:
                        if (
                            command.authorization.mode
                            == AuthorizationMode.PROHIBITED
                            and command.operation
                        ):
                            warnings.append(
                                f"prohibited_command_defined:"
                                f"{command.command_id}"
                            )

    def _validate_dependencies(
        self,
        plan_version: PlanVersion,
        errors: list[str],
    ) -> None:
        try:
            build_dependency_graph(
                plan_version.mission,
                plan_version.dependencies,
            )
        except PlanningValidationError as exc:
            if exc.violations:
                errors.extend(exc.violations)
            else:
                errors.append(str(exc))
        except ValueError as exc:
            errors.append(str(exc))

    def _validate_risks(
        self,
        mission: Mission,
        warnings: list[str],
    ) -> None:
        risks = list(mission.risks)

        for objective in mission.objectives:
            risks.extend(objective.risks)

            for task in objective.tasks:
                risks.extend(task.risks)

                for activity in task.activities:
                    risks.extend(activity.risks)

                    for command in activity.commands:
                        risks.extend(command.risks)

        for risk in risks:
            if not risk.owner:
                warnings.append(f"risk_has_no_owner:{risk.risk_id}")

            if not risk.mitigation:
                warnings.append(f"risk_has_no_mitigation:{risk.risk_id}")

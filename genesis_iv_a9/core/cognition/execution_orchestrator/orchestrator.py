from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Mapping

from .contracts import (
    ActivityExecutionRecord,
    ActivityExecutionSpec,
    ExecutionContext,
    ExecutionObservation,
    MissionExecutionRequest,
    MissionExecutionSnapshot,
    utc_now_iso,
)
from .enums import (
    DispatchMode,
    ExecutionStatus,
    MissionExecutionStatus,
    ObservationKind,
)
from .errors import (
    ExecutionApprovalRequiredError,
    InvalidExecutionPlanError,
)
from .executors import ExecutorRegistry
from .state import validate_transition


def _stable_id(prefix: str, *parts: str) -> str:
    payload = "|".join(parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:24]}"


class ExecutiveExecutionOrchestrator:
    """Controlled, deterministic coordinator for Mission Plan activities."""

    def __init__(self, registry: ExecutorRegistry | None = None) -> None:
        self._registry = registry or ExecutorRegistry()

    @property
    def registry(self) -> ExecutorRegistry:
        return self._registry

    def create_snapshot(
        self,
        request: MissionExecutionRequest,
    ) -> MissionExecutionSnapshot:
        self._validate_request(request)
        now = utc_now_iso()
        records = tuple(
            ActivityExecutionRecord(
                activity_id=activity_id,
                status=ExecutionStatus.PENDING,
                attempt=0,
            )
            for activity_id in request.topological_order
        )
        return MissionExecutionSnapshot(
            execution_id=_stable_id(
                "execution",
                request.mission_id,
                request.decision_id,
                request.request_id,
            ),
            mission_id=request.mission_id,
            decision_id=request.decision_id,
            status=MissionExecutionStatus.CREATED,
            activities=records,
            observations=(),
            policy_id=request.policy_id,
            constitution_revision=request.constitution_revision,
            created_at=now,
            updated_at=now,
        )

    def run_ready(
        self,
        request: MissionExecutionRequest,
        snapshot: MissionExecutionSnapshot,
        approvals: Mapping[str, bool] | None = None,
    ) -> MissionExecutionSnapshot:
        approvals = approvals or {}
        specs = {item.activity_id: item for item in request.activities}
        records = {item.activity_id: item for item in snapshot.activities}
        observations = list(snapshot.observations)

        for activity_id in request.topological_order:
            spec = specs[activity_id]
            record = records[activity_id]

            if record.status in {
                ExecutionStatus.SUCCEEDED,
                ExecutionStatus.CANCELLED,
                ExecutionStatus.ROLLED_BACK,
            }:
                continue

            dependencies_succeeded = all(
                records[dependency_id].status is ExecutionStatus.SUCCEEDED
                for dependency_id in spec.dependency_ids
            )
            if not dependencies_succeeded:
                continue

            if record.status is ExecutionStatus.PENDING:
                record = self._transition(record, ExecutionStatus.READY)
                records[activity_id] = record

            if record.status is not ExecutionStatus.READY:
                continue

            approved = bool(approvals.get(activity_id, False))
            if spec.requires_approval and not approved:
                records[activity_id] = self._transition(
                    record,
                    ExecutionStatus.BLOCKED,
                    summary="Explicit approval is required.",
                )
                observations.append(
                    self._observation(
                        request,
                        activity_id,
                        ObservationKind.EXECUTION_BLOCKED,
                        "Activity blocked pending explicit approval.",
                    )
                )
                continue

            if spec.dispatch_mode is DispatchMode.HUMAN:
                records[activity_id] = self._transition(
                    record,
                    ExecutionStatus.BLOCKED,
                    summary="Human execution is required.",
                )
                observations.append(
                    self._observation(
                        request,
                        activity_id,
                        ObservationKind.EXECUTION_BLOCKED,
                        "Activity requires human execution and confirmation.",
                    )
                )
                continue

            running = self._transition(
                record,
                ExecutionStatus.RUNNING,
                attempt=record.attempt + 1,
                started_at=utc_now_iso(),
            )
            records[activity_id] = running
            observations.append(
                self._observation(
                    request,
                    activity_id,
                    ObservationKind.EXECUTION_STARTED,
                    f"Activity execution attempt {running.attempt} started.",
                )
            )

            executor = self._registry.resolve(spec.required_capability)
            try:
                result = executor.execute(
                    ExecutionContext(
                        mission_id=request.mission_id,
                        decision_id=request.decision_id,
                        activity=spec,
                        attempt=running.attempt,
                        approved=approved,
                    )
                )
            except Exception as exc:
                result = None
                failure_message = f"{type(exc).__name__}: {exc}"
            else:
                failure_message = ""

            if result is not None and result.succeeded:
                records[activity_id] = self._transition(
                    running,
                    ExecutionStatus.SUCCEEDED,
                    completed_at=utc_now_iso(),
                    summary=result.summary,
                    output_reference=result.output_reference,
                )
                observations.append(
                    self._observation(
                        request,
                        activity_id,
                        ObservationKind.EXECUTION_SUCCEEDED,
                        result.summary,
                    )
                )
                continue

            summary = (
                result.summary if result is not None else failure_message
            )
            failed = self._transition(
                running,
                ExecutionStatus.FAILED,
                completed_at=utc_now_iso(),
                summary=summary,
                error=failure_message,
            )
            records[activity_id] = failed
            observations.append(
                self._observation(
                    request,
                    activity_id,
                    ObservationKind.EXECUTION_FAILED,
                    summary or "Activity execution failed.",
                )
            )

            if failed.attempt < spec.max_attempts:
                records[activity_id] = self._transition(
                    failed,
                    ExecutionStatus.READY,
                    summary="Retry scheduled.",
                )
                observations.append(
                    self._observation(
                        request,
                        activity_id,
                        ObservationKind.RETRY_SCHEDULED,
                        f"Retry {failed.attempt + 1} of {spec.max_attempts} scheduled.",
                    )
                )
            elif spec.rollback_instruction:
                records[activity_id] = self._transition(
                    failed,
                    ExecutionStatus.ROLLBACK_PENDING,
                    summary="Rollback requested.",
                )
                observations.append(
                    self._observation(
                        request,
                        activity_id,
                        ObservationKind.ROLLBACK_REQUESTED,
                        spec.rollback_instruction,
                    )
                )

        ordered_records = tuple(
            records[activity_id] for activity_id in request.topological_order
        )
        mission_status = self._mission_status(ordered_records)
        return replace(
            snapshot,
            status=mission_status,
            activities=ordered_records,
            observations=tuple(observations),
            updated_at=utc_now_iso(),
        )

    def confirm_human_completion(
        self,
        request: MissionExecutionRequest,
        snapshot: MissionExecutionSnapshot,
        activity_id: str,
        *,
        succeeded: bool,
        summary: str,
    ) -> MissionExecutionSnapshot:
        specs = {item.activity_id: item for item in request.activities}
        if activity_id not in specs:
            raise InvalidExecutionPlanError(
                f"Unknown activity {activity_id!r}."
            )
        spec = specs[activity_id]
        if spec.dispatch_mode not in {DispatchMode.HUMAN, DispatchMode.HYBRID}:
            raise InvalidExecutionPlanError(
                "Human confirmation is only valid for human or hybrid activities."
            )

        records = {item.activity_id: item for item in snapshot.activities}
        current = records[activity_id]
        if current.status is ExecutionStatus.PENDING:
            current = self._transition(current, ExecutionStatus.READY)
        if current.status is ExecutionStatus.BLOCKED:
            current = self._transition(current, ExecutionStatus.READY)
        running = self._transition(
            current,
            ExecutionStatus.RUNNING,
            attempt=current.attempt + 1,
            started_at=utc_now_iso(),
        )
        target = (
            ExecutionStatus.SUCCEEDED if succeeded else ExecutionStatus.FAILED
        )
        records[activity_id] = self._transition(
            running,
            target,
            completed_at=utc_now_iso(),
            summary=summary,
        )
        observation = self._observation(
            request,
            activity_id,
            (
                ObservationKind.EXECUTION_SUCCEEDED
                if succeeded
                else ObservationKind.EXECUTION_FAILED
            ),
            summary,
        )
        ordered = tuple(records[item] for item in request.topological_order)
        return replace(
            snapshot,
            status=self._mission_status(ordered),
            activities=ordered,
            observations=snapshot.observations + (observation,),
            updated_at=utc_now_iso(),
        )

    def confirm_rollback(
        self,
        request: MissionExecutionRequest,
        snapshot: MissionExecutionSnapshot,
        activity_id: str,
        summary: str,
    ) -> MissionExecutionSnapshot:
        records = {item.activity_id: item for item in snapshot.activities}
        current = records[activity_id]
        records[activity_id] = self._transition(
            current,
            ExecutionStatus.ROLLED_BACK,
            completed_at=utc_now_iso(),
            summary=summary,
        )
        ordered = tuple(records[item] for item in request.topological_order)
        return replace(
            snapshot,
            status=self._mission_status(ordered),
            activities=ordered,
            observations=snapshot.observations
            + (
                self._observation(
                    request,
                    activity_id,
                    ObservationKind.ROLLBACK_COMPLETED,
                    summary,
                ),
            ),
            updated_at=utc_now_iso(),
        )

    def _validate_request(self, request: MissionExecutionRequest) -> None:
        ids = [item.activity_id for item in request.activities]
        if len(ids) != len(set(ids)):
            raise InvalidExecutionPlanError(
                "Activity identifiers must be unique."
            )
        if tuple(ids) != tuple(request.topological_order):
            if set(ids) != set(request.topological_order):
                raise InvalidExecutionPlanError(
                    "topological_order must contain every activity exactly once."
                )
        known = set(ids)
        position = {
            activity_id: index
            for index, activity_id in enumerate(request.topological_order)
        }
        for activity in request.activities:
            for dependency_id in activity.dependency_ids:
                if dependency_id not in known:
                    raise InvalidExecutionPlanError(
                        f"Unknown dependency {dependency_id!r}."
                    )
                if position[dependency_id] >= position[activity.activity_id]:
                    raise InvalidExecutionPlanError(
                        "topological_order violates dependency ordering."
                    )

    def _transition(
        self,
        record: ActivityExecutionRecord,
        target: ExecutionStatus,
        **changes,
    ) -> ActivityExecutionRecord:
        validate_transition(record.status, target)
        return replace(record, status=target, **changes)

    def _mission_status(
        self,
        records: tuple[ActivityExecutionRecord, ...],
    ) -> MissionExecutionStatus:
        statuses = {item.status for item in records}
        if all(status is ExecutionStatus.SUCCEEDED for status in statuses):
            return MissionExecutionStatus.SUCCEEDED
        if ExecutionStatus.ROLLBACK_PENDING in statuses:
            return MissionExecutionStatus.FAILED
        if ExecutionStatus.FAILED in statuses:
            return MissionExecutionStatus.FAILED
        if ExecutionStatus.BLOCKED in statuses:
            return MissionExecutionStatus.BLOCKED
        if ExecutionStatus.CANCELLED in statuses:
            return MissionExecutionStatus.CANCELLED
        return MissionExecutionStatus.RUNNING

    def _observation(
        self,
        request: MissionExecutionRequest,
        activity_id: str,
        kind: ObservationKind,
        message: str,
    ) -> ExecutionObservation:
        observation_id = _stable_id(
            "observation",
            request.mission_id,
            activity_id,
            kind.value,
            message,
        )
        return ExecutionObservation(
            observation_id=observation_id,
            mission_id=request.mission_id,
            activity_id=activity_id,
            kind=kind,
            message=message,
            created_at=utc_now_iso(),
        )

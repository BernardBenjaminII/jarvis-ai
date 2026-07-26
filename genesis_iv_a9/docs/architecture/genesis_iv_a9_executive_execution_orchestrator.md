# Genesis IV-A9 — Executive Execution Orchestrator

## Purpose

Genesis IV-A9 consumes a validated Mission Plan and coordinates controlled
activity execution.

It owns lifecycle state, dependency-aware scheduling, executor dispatch,
approval gates, retries, rollback requests, telemetry, and execution
observations.

## Boundary

The orchestrator does not provide an unrestricted shell, directly invoke
arbitrary operating-system commands, or bypass human approval.

Concrete capabilities are supplied through registered executor adapters.

## Lifecycle

Activity lifecycle:

`PENDING → READY → RUNNING → SUCCEEDED`

Failure paths:

`RUNNING → FAILED → READY` for retry

`RUNNING → FAILED → ROLLBACK_PENDING → ROLLED_BACK`

Approval or human paths may enter `BLOCKED` until explicitly resumed or
confirmed.

## Dependency Scheduling

Activities become ready only after all declared dependencies succeed.
The incoming topological order is validated before execution begins.

## Executor Registry

Executors are registered by stable capability identifier. The orchestrator
resolves the activity's required capability and dispatches an immutable
Execution Context.

This isolates orchestration from tools, APIs, subprocesses, and platform-
specific implementations.

## Observability

Every lifecycle event emits an immutable Execution Observation. These
observations are suitable for publication to the Observation Bus, closing the
Executive loop:

Observe → Reason → Decide → Plan → Execute → Observe

## Determinism

Execution identity derives from mission, decision, and request identifiers.
Scheduling order follows the Mission Plan's validated topological order.

Wall-clock timestamps are telemetry and do not participate in identity.

# ADR-0036 — Executive Execution Orchestrator Boundary

**Status:** Accepted  
**Milestone:** Genesis IV-A9

## Context

Genesis IV-A8 produces immutable Mission Plans but intentionally does not
execute them. Execution requires explicit lifecycle control, dependency-aware
scheduling, authority gates, retry policy, rollback coordination, and
observability.

## Decision

Create `core.cognition.execution_orchestrator` as the canonical owner of
controlled Mission Plan execution coordination.

The orchestrator shall:

- validate execution projections before dispatch;
- preserve Mission and Decision identity;
- enforce activity dependency order;
- require explicit approval when configured;
- isolate concrete execution behind capability adapters;
- maintain immutable execution snapshots;
- support bounded retries;
- request and confirm rollback;
- emit immutable execution observations; and
- avoid unrestricted command execution.

## Consequences

JARVIS gains a controlled action boundary without embedding platform-specific
or unsafe execution mechanisms in cognition. Concrete executors remain
independently governable, auditable, and replaceable.

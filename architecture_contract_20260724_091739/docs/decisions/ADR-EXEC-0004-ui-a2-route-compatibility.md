# ADR-EXEC-0004 — Preserve UI-A2 Routes as Compatibility Aliases

**Status:** Accepted

## Context

Genesis VI-A3 introduced the Executive Projection Bus under
`/operations/bridge/*`. Restoring `operations.py` from Git HEAD removed the
older UI-A2 route surface even though later capability and knowledge phases
still certified against it.

## Decision

Preserve the UI-A2 routes as append-only compatibility aliases. They delegate
to the canonical Executive Integration runtime. Preserve the VI-A3 Bridge
routes unchanged.

## Consequences

- Existing UI-A2 clients remain compatible.
- VI-A3 clients retain normalized Bridge and readiness endpoints.
- No projection or capability registry is duplicated.
- Route removal requires a future explicit deprecation ADR and migration plan.

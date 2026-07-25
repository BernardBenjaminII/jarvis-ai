# ADR-0032: Executive Course-of-Action Generation Boundary

**Status:** Accepted

## Decision

Genesis IV-A6.2 introduces `core.cognition.coa` as the canonical owner of executive course-of-action generation. A COA is a cognitive candidate strategy, not an executable plan.

The subsystem consumes the public shape of IV-A5 reasoning results, emits deterministic COAs, and exposes neutral decision-alternative data for IV-A6.1. It must not import `core.executive.planning` or `core.operations`.

## Consequences

Decision synthesis receives multiple auditable candidates. Planning and operations retain ownership of decomposition and execution. This prevents cognition from bypassing executive governance.

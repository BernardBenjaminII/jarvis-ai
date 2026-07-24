# ADR-0024: Cognitive Workspace Integration Engine

**Status:** Accepted  
**Decision:** Genesis III-A4

## Context

The Cognitive Workspace foundation, repository, and catalog were independently certified, but no canonical application boundary assembled domain inputs into a persisted workspace.

## Decision

Introduce `core.cognition.integration` as a thin, deterministic layer over the certified workspace public API. Integration contracts are immutable. The pipeline maps seeds into canonical workspace models. The service owns repository coordination. The director exposes a stable future-facing orchestration boundary.

## Consequences

Cognitive state becomes inspectable, resumable, and replayable without coupling Genesis III to Executive execution, network access, knowledge acquisition, or inference policy. Existing workspace contracts are reused rather than duplicated.

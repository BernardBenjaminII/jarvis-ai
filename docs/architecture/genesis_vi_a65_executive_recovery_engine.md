# Genesis VI-A6.5 — Executive Recovery Engine

**Status:** Implemented  
**Depends on:** Genesis VI-A6.4 Executive Integrity Engine

## Principle

Recovery never decides whether state is trustworthy. It obeys an Integrity Report.

```text
Repository → Integrity Certification → Recovery Policy → Reconstruction → Recovery Report
```

## Policies

- latest certified
- latest recoverable certified prefix
- exact sequence
- exact checkpoint identifier
- exact checkpoint fingerprint

A fallback is legal only when the complete prefix ending at the selected checkpoint is independently certified.

## Evidence

Each successful recovery records the selected checkpoint, policy, Integrity Report fingerprint, fallback status, recovered-state fingerprint, and Recovery Report fingerprint.

## Non-goals

Replay, schema migration, distributed reconciliation, external side-effect resumption, and session orchestration remain later phases.

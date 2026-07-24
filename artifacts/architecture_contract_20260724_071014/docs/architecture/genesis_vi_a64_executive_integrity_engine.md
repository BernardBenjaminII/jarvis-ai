# Genesis VI-A6.4 — Executive Integrity Engine

**Status:** Implemented  
**Authority:** ADR-0023 — Executive Evidence and Trust Model

## Constitutional Law

> No executive state shall be restored, replayed, or acted upon unless its checkpoint history has been verified for integrity, ordering, provenance, and continuity.

## Architecture

```text
Checkpoint Repository
        ↓
Integrity Scanner
        ↓
Integrity Evaluator
        ↓
Immutable Integrity Report
        ↓
Recovery / Replay
```

The scanner records facts without policy judgments. The evaluator maps facts to severity and disposition. The report is immutable, deterministic evidence. The engine is the stable public façade.

## Verified Conditions

- sequence continuity and uniqueness
- parent-chain continuity
- payload digest integrity
- checkpoint digest integrity
- schema compatibility
- repository accessibility
- deterministic report and repository fingerprints

## Dispositions

`TRUSTED`, `RECOVERABLE`, `REQUIRES_MIGRATION`, `QUARANTINE`, and `UNRECOVERABLE`.

## Non-Responsibilities

This phase never deletes, moves, restores, replays, or migrates persisted evidence. Those actions belong to later phases.

# Genesis VII-A0 — Pack 4A-3.2

## Timeline Repository Isolation & Concurrency Safety

**Status:** Implemented

## Reproduced Defect

A stale Event Bus loaded a repository containing two events. Other application
lifespans advanced the shared JSONL authority to sequence fourteen. The stale
bus later generated `executive_shutdown_started` as sequence three and appended
it as record fifteen.

The repository correctly refused that history at the next startup:

```text
Sequence mismatch: expected 15, found 3.
Broken chain before sequence 3.
```

## Corrective Architecture

```text
Publisher emits TimelineEventDraft
        ↓
Event Bus creates candidate event
        ↓
Repository acquires interprocess lock
        ↓
Repository reloads certified disk authority
        ↓
Candidate validation
        ├── valid: append + fsync
        └── stale: conflict
                    ↓
             Event Bus reloads
             rebuilds engine
             retries draft once
```

## Protections

- repository-local interprocess lock;
- disk-authoritative validation before every append;
- no stale in-memory append without conflict detection;
- one bounded stale-writer retry;
- runtime root environment support;
- explicit test timeline isolation;
- multiprocess regression coverage;
- corruption-preserving recovery utility.

## Runtime Root Resolution

Priority:

1. `JARVIS_EXECUTIVE_TIMELINE_ROOT`;
2. `JARVIS_RUNTIME_ROOT/executive/timeline`;
3. `JARVIS_RUNTIME/executive/timeline`;
4. legacy project-relative development fallback.

Production launchers should set `JARVIS_RUNTIME_ROOT`.

## Test Isolation

Tests that enter the FastAPI lifespan run in subprocesses with a unique
temporary `JARVIS_EXECUTIVE_TIMELINE_ROOT`. Verification can no longer append
boot or shutdown events into the operational development history.

## Recovery Utility

Dry-run audit:

```bash
python dev/tools/executive_timeline_recover.py \
    artifacts/runtime/executive_timeline/executive.timeline.jsonl
```

Preserve the original and truncate to the longest certified prefix:

```bash
python dev/tools/executive_timeline_recover.py \
    artifacts/runtime/executive_timeline/executive.timeline.jsonl \
    --apply
```

## Certification

The pack reproduces stale in-memory writers using two Event Bus instances and
uses two spawned processes to certify one uninterrupted sequence and
fingerprint chain.

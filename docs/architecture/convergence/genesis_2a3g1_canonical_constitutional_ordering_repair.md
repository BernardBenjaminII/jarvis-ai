# Genesis II-A3G.1 — Canonical Constitutional Ordering Repair

**Classification:** Maintenance release
**Predecessor:** Genesis II-A3G

## Defect

Genesis II-A3G admitted Roman runtime roots such as:

```text
dev/verify_genesis_ix_0.sh
```

For backward compatibility, the runtime root retained the internal stream and
display label `IX-Z0`. The default dataclass comparator consequently ranked it
after `IX-A1`, despite the manifest correctly placing the runtime root first.

## Repair

II-A3G.1 separates constitutional order from compatibility presentation.

A phase now carries a non-identity `phase_kind`:

- `root` — Roman runtime campaign root;
- `branch` — ordinary numeric or Roman stream phase.

The constitutional comparator uses:

```text
generation
phase kind
stream
hierarchy
```

Therefore:

```text
IX-0 < IX-A0 < IX-A1 < IX-A1.1 < IX-A2 < IX-B0
```

while the legacy runtime-root label remains `IX-Z0`.

## Non-Goals

- No verifier filename grammar changes.
- No legacy label changes.
- No certified phase identity changes.
- No FastAPI or runtime changes.

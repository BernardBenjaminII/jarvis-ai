# Genesis IV-B4C — Canonical Migration Registry Reconstruction

## Mission

Reconstruct the Observation migration registry as a complete deterministic
artifact rather than continuing incremental textual modifications.

## Registry Ownership

The registry governs direct Observation definitions only:

| Path | Status | Target |
|---|---|---|
| `core/observation/contracts.py` | Canonical | `Observation` |
| `core/cognition/common/contracts.py` | Approved Legacy | Canonical adapter |
| `core/cognition/observation/models.py` | Deprecated Rename | `ObservationRecord` |
| `core/representation/contracts.py` | Deprecated Rename | `RepresentedStatement` |

`core/cognition/contracts.py` is excluded because it is a public re-export
surface rather than a direct Observation definition.

## Invariants

- Exactly one canonical owner exists.
- Registry paths are unique.
- Approved legacy contracts must have adapters.
- Deprecated definitions must have adapters and semantic target names.
- Registry serialization and fingerprinting are deterministic.
- Every direct Observation definition under `core/` must be governed.

## Outcome

IV-B4C restores a valid Python module and establishes the registry as the
single source of truth for controlled Observation migration.

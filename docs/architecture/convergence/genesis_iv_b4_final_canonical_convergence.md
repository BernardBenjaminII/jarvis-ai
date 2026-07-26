# Genesis IV-B4 — Final Canonical Observation Convergence

## Mission

Complete the Observation convergence program by replacing layered corrective
patches with one coherent canonical implementation.

## Canonical Pipeline

Reality → Extraction → Observation Candidate → Normalization → Confidence →
Canonical Observation → Observation Bus → Snapshot → Situation → Evidence →
Reasoning

## Final Ownership Model

| Module | Classification | Treatment |
|---|---|---|
| `core/observation/contracts.py` | Canonical definition | Permanent owner |
| `core/cognition/common/contracts.py` | Approved legacy definition | Adapter-backed migration |
| `core/cognition/observation/models.py` | Deprecated definition | Rename to `ObservationRecord` |
| `core/representation/contracts.py` | Deprecated definition | Rename to `RepresentedStatement` |
| `core/cognition/contracts.py` | Public re-export | Not a definition owner |

## Compatibility Contract

The final package preserves the historical IV-B4 API:

- `MIGRATION_ENTRIES`
- `MIGRATION_SCHEMA_VERSION`
- `migration_entry_for_path()`

It also provides the canonical deterministic API:

- `OBSERVATION_MIGRATION_REGISTRY`
- `migration_entries()`
- `migration_entry_for()`
- `migration_registry_payload()`
- `migration_registry_fingerprint()`

The old and new registry names reference the same immutable tuple.

## Audit Contract

The audit uses Python AST discovery and recognizes only direct top-level
`class Observation` definitions. Imports, aliases, and public re-exports do
not create governance ownership.

No function is redefined later in the module. Export filtering is integrated
directly into the canonical audit implementation.

## Certification Standard

Certification requires:

- complete Python compilation;
- preservation of historical public imports;
- deterministic registry fingerprinting;
- exactly one canonical Observation owner;
- governance of every direct Observation definition;
- exclusion of public re-exports from ownership;
- no forbidden duplicates;
- successful IV-B3 through IV-B4 regression.

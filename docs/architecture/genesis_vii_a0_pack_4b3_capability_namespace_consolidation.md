
# Genesis VII-A0 Pack 4B-3 — Capability Namespace Consolidation

**Status:** Implemented
**Predecessor:** Genesis VII-A0 Pack 4B-2
**Purpose:** Eliminate the Python module/package collision at
`core.executive.capabilities`.

## Problem

The repository contained both:

```text
core/executive/capabilities.py
core/executive/capabilities/
```

Python resolved `core.executive.capabilities` to the package after Pack 4B-2 was
installed. Existing consumers such as `ExecutiveDirector` and
`DirectorRegistry` still expected legacy symbols including
`DirectorReadiness`, causing application startup to fail.

## Decision

The historical module is migrated to:

```text
core/executive/capability_contracts.py
```

The package:

```text
core/executive/capabilities/
```

becomes the single canonical public namespace. It re-exports every public legacy
contract and every Pack 4B-2 orchestration contract.

## Compatibility Guarantees

1. `from core.executive.capabilities import DirectorReadiness` remains valid.
2. `from core.executive.capabilities import CapabilityOrchestrator` remains valid.
3. Existing imports in `director.py` and `registry.py` require no modification.
4. The ambiguous `core/executive/capabilities.py` path no longer exists.
5. The legacy module contents are moved unchanged.
6. Installer backups are created before any move or replacement.
7. FastAPI application import is part of certification.

## Rollback

The installer retains timestamped copies under:

```text
.migration_backups/genesis_vii_a0_pack_4b3_YYYYMMDD_HHMMSS/
```

# Genesis III-F1 — Cognitive Workspace Integration Freeze

## Purpose

Genesis III-F1 freezes the certified Cognitive Workspace architecture after Genesis III-A1 through III-A4. It establishes a deterministic baseline for package structure, public exports, dependency direction, module content, and executive readiness.

## Canonical architecture

```text
core.cognition.workspace
        ↓
core.cognition.integration
        ↓
future executive consumers
```

The workspace package must not depend on integration or executive layers. The integration package may consume workspace contracts but must not depend on executive, mission, route, or operations implementations.

## Certification artifacts

The freeze produces and verifies:

- `genesis_3f1_public_api.json` and `.md`
- `genesis_3f1_dependency_graph.json` and `.md`
- `genesis_3f1_snapshot.json`
- `genesis_3f1_executive_readiness.md`

The architecture fingerprint is derived only from deterministic repository content and audit results. Timestamps and mutable environment details are excluded from the fingerprint.

## Change policy

Any intentional change to Genesis III package files, exports, or dependencies must regenerate the baseline with:

```bash
PYTHON_BIN=/path/to/python \
python dev/tools/audit_genesis_3f1.py --write
```

The resulting fingerprint change must be reviewed and committed as an explicit architectural evolution. Silent drift causes verification failure.

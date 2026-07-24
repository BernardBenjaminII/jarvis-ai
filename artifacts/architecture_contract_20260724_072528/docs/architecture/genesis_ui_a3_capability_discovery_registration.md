# Genesis UI-A3 — Capability Discovery & Registration

## Objective

Populate the canonical `CapabilityRegistry` with real, bound capabilities and
discover additional subsystem capability hooks without coupling FastAPI to
domain implementations.

## Built-in capabilities

UI-A3 registers seven real, read-only Operations capabilities:

- `operations.status`
- `operations.executive`
- `operations.health`
- `operations.missions`
- `operations.resources`
- `operations.timeline`
- `operations.events`

Each capability is bound directly to the process-wide `OperationsService`.

## Discovery protocol

Packages participate by exposing:

```python
def register_capabilities(registry: CapabilityRegistry) -> None:
    ...
```

Configured roots are supplied through:

```bash
export JARVIS_CAPABILITY_PACKAGES="core.knowledge,core.reasoning"
```

The discovery engine:

1. imports each root
2. walks submodules recursively
3. invokes hooks deterministically
4. records successful and failed imports
5. records how many capabilities each hook registered
6. preserves all failures in the capability projection

## Safety boundary

UI-A3 exposes discovery and binding metadata only.

It does not add a remote execution endpoint. Governed execution belongs to
UI-A4 and must include authority, dry-run, audit, provenance, and policy checks.

## Projection contract

Each capability now exposes:

- identifier
- display name
- description
- domain
- subsystem
- implementation
- order
- requirements
- provided tokens
- binding state
- operations
- destructive flag
- dry-run support
- tags
- source
- version

## Health normalization

The Operations projection now recognizes both `status` and `state`, mapping the
existing `healthy` response to `available`.

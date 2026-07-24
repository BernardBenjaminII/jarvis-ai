# Executive Integration Architecture

## 1. Problem statement

JARVIS contains mature implementations across acquisition, cognition, executive control, knowledge, reasoning, representation, operations, planning, memory, and runtime management. Those systems do not yet present a single coherent operational surface.

The integration gap appears in four forms:

1. **Discovery gap** — the interface cannot enumerate everything JARVIS can do.
2. **Projection gap** — backend state is not consistently projected into stable API resources.
3. **Execution gap** — visible UI controls are not always bound to real operations.
4. **Transparency gap** — evidence, provenance, confidence, failure, and missing knowledge are not uniformly exposed.

Genesis UI-A closes those gaps.

## 2. Canonical integration plane

The canonical architecture is:

```text
Domain subsystem
    |
    v
Domain service or facade
    |
    v
Executive Integration Plane
    |-- capability registry
    |-- state projection
    |-- command dispatch
    |-- authorization/policy
    |-- provenance/audit
    |-- health/degradation
    |
    v
Stable REST/SSE/WebSocket contracts
    |
    v
Mission Control UI
```

The Executive Integration Plane does not replace domain logic. It normalizes how domain logic is discovered, observed, invoked, and audited.

## 3. Mandatory integration concepts

### 3.1 Capability descriptor

Every user-addressable capability must declare:

- stable identifier
- display name
- owning subsystem
- description
- lifecycle status
- availability
- supported operations
- required inputs
- produced outputs
- permission level
- health state
- degradation reason
- evidence/provenance behavior
- UI placement hints

### 3.2 State projection

Every subsystem must expose a read-only projection suitable for the UI. The projection must contain live data, not placeholders.

A projection must distinguish:

- `available`
- `degraded`
- `unavailable`
- `unknown`
- `not_configured`

### 3.3 Command envelope

All state-changing actions use a command envelope:

```json
{
  "command_id": "uuid",
  "capability_id": "knowledge.ingest",
  "operation": "execute",
  "requested_at": "RFC3339",
  "requested_by": "operator",
  "arguments": {},
  "dry_run": false,
  "correlation_id": "uuid"
}
```

### 3.4 Result envelope

All command results use:

```json
{
  "command_id": "uuid",
  "status": "accepted|running|completed|failed|rejected",
  "started_at": "RFC3339|null",
  "completed_at": "RFC3339|null",
  "summary": "human-readable outcome",
  "data": {},
  "artifacts": [],
  "evidence": [],
  "warnings": [],
  "errors": [],
  "audit_event_id": "stable-id"
}
```

## 4. UI information architecture

The primary navigation should represent JARVIS cognitive and executive functions:

1. Commander Brief
2. Missions
3. Knowledge
4. Reasoning
5. Memory
6. Capabilities
7. Acquisition
8. Operations
9. Runtime
10. Governance

The interface must derive feature availability from the integration plane rather than hard-coded assumptions.

## 5. Data ownership

Domain packages own their data and business rules. The integration plane owns:

- discovery
- normalized projections
- transport contracts
- command routing
- cross-domain correlation
- audit events
- UI visibility

The frontend must never read internal databases directly.

## 6. Non-negotiable constraints

- No fabricated telemetry.
- No UI action without a real command path.
- No hidden failure state.
- No opaque confidence score.
- No knowledge answer without provenance where provenance exists.
- No capability marked operational unless its health check passes.
- No destructive action without explicit policy and confirmation semantics.

# Genesis VI-A2 — Executive Mission Control

## Status

Implementation deliverable.

> Repository note: the identifier `Genesis VI-A2` already exists in this repository for deterministic working memory. This document uses the qualified name **Genesis VI-A2 Executive Mission Control** and unique verifier filenames to preserve historical artifacts without destructive renaming.

## Objective

Expose the canonical `ExecutiveSnapshot` through the existing MC-1001 Operations boundary and render it in the MC-1002 Commander's Bridge without creating direct browser dependencies on Executive, Reasoning, Cognition, or Mission internals.

## Architectural boundary

The browser consumes only `/operations/*` routes. The new endpoint is:

```text
GET /operations/executive
```

It returns `OperationsService.executive().to_dict()`. The existing `/operations/status` aggregate remains compatible and continues to include the same Executive projection.

## Interface surface

The bridge displays:

- Executive state and readiness
- Active mission identifier
- Active objective identifier
- Current activity
- Last state transition
- Observation, inference, and plan counts
- Pending decisions and recommendations
- Existing mission, health, resource, timeline, and alert projections

## Refresh model

The client performs an immediate refresh and then polls every 15 seconds. Each endpoint fails independently so partial operational visibility remains available during a degraded subsystem response.

## Timeline integration

The client recognizes the canonical `TimelineSnapshot.entries` field and preserves support for legacy list-like payloads. Timeline data remains owned by `OperationsEventRegistry` and `TimelineAdapter`.

## Safety and compatibility

- No command execution endpoint is introduced.
- The interface remains read-only.
- No direct `/executive/*`, `/reasoning/*`, or `/cognition/*` browser calls are permitted.
- Existing MC-1001 and MC-1002 tests remain part of certification.
- The original working-memory `dev/verification/verify_genesis_vi_a2.py` is not replaced.

# MC-1001 — Executive Operations Interface

## Status

Implemented by Sprint 0.

## Purpose

The Operations subsystem is the stable boundary between the JARVIS Executive
Operating System and all current or future clients.

Clients include:

- Mission Control web interface
- CLI tools
- desktop and mobile applications
- voice interfaces
- Meta Quest interfaces
- autonomous operational agents

## Architectural Rule

Operations aggregates and projects state. It does not own Executive, Reasoning,
Knowledge, Evidence, Representation, or Bootstrap state.

No lower subsystem may import `core.operations`.

## Sprint 0 Capabilities

- immutable operational snapshots
- deterministic serialization
- deterministic snapshot fingerprints under a fixed clock and fixed providers
- mission projection
- component health aggregation
- runtime resource projection
- canonical event storage
- operational timeline projection
- FastAPI read endpoints

## API

- `GET /operations/status`
- `GET /operations/health`
- `GET /operations/missions`
- `GET /operations/resources`
- `GET /operations/timeline`
- `GET /operations/events`

## Deferred Work

The following are intentionally deferred:

- WebSocket event streaming
- persistent event storage
- pause and resume commands
- checkpoint and replay commands
- direct Executive adapters
- authentication and authorization
- Commander Dashboard UI

These belong to later Mission Control sprints.

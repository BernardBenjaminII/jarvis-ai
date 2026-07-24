# JARVIS Gen 2 Phase I — Executive Director and Mission Engine

## Status

Implemented as the first additive milestone of JARVIS Generation 2.

## Purpose

Generation 1 established the Knowledge Engine, Knowledge Director,
explainable ranking, integrity checks, self-healing, runtime discovery, and
the Doctor framework.

Generation 2 introduces a supervisory intelligence layer. The first milestone
provides the contracts and lifecycle required for JARVIS to convert an
objective into a persistent mission, divide it into tasks, route each task to
a director, execute dependencies in order, audit state transitions, and
synthesize results.

## Architecture

```text
User Objective
      |
      v
ExecutiveDirector
      |
      +-- MissionPlanner
      |       |
      |       +-- deterministic task graph
      |
      +-- MissionEngine
      |       |
      |       +-- DirectorRegistry
      |       |       +-- executive
      |       |       +-- knowledge
      |       |       +-- system
      |       |
      |       +-- dependency execution
      |       +-- failure propagation
      |       +-- synthesis
      |
      +-- MissionStore
              +-- mission snapshots
              +-- lifecycle events
```

## Design decisions

### Additive architecture

Gen 2 does not replace the Knowledge Engine. It sits above it and delegates to
it through a stable bridge contract.

### Deterministic first planner

The first planner is deterministic and auditable. It uses explicit routing
rules rather than an LLM. A later planner may use a language model behind the
same `MissionPlanner` interface.

### Persistent missions

Missions are stored in SQLite. Every significant lifecycle transition is also
written to the `mission_events` table.

### Director isolation

The engine depends only on the `DirectorHandler` protocol. Directors may later
be local Python services, subprocesses, remote services, OS specialists, or
autonomous agents.

### Safe system behavior

The Phase I system director is assessment-only. It cannot modify the host.
Guarded execution, approval policies, and rollback belong to a later phase.

## Mission lifecycle

```text
draft
  -> planned
  -> running
  -> completed

running
  -> failed
  -> blocked

draft/planned/running
  -> cancelled
```

## Phase I completion criteria

- Mission domain models compile.
- SQLite persistence initializes automatically.
- Mission plans reject missing or cyclic dependencies.
- Tasks execute only after dependencies complete.
- Director failures are captured and propagated.
- Mission and task events are auditable.
- Knowledge tasks route through a bridge contract.
- System tasks remain non-destructive.
- CLI submission and inspection work.
- Unit and smoke tests pass.

## Next phase

Gen 2 Phase II should connect the existing Knowledge Director to
`KnowledgeHandler`, add capability declarations, and let the Executive
Director select among real registered directors based on capabilities rather
than keyword rules alone.

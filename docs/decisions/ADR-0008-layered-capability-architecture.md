# ADR-0008 — Layered Capability Architecture

**Status:** Accepted

**Date:** 2026-07-06

---

# Context

The JARVIS Knowledge Engine has grown from a collection of independent command-line
utilities into a unified knowledge platform.

Early implementations exposed functionality primarily through CLI entry points.

Examples include:

- discovery_cli.py
- object_builder_cli.py
- registry_cli.py
- validation_cli.py
- librarian_cli.py

As the Knowledge Engine evolved, additional execution environments appeared:

- Workflow Engine
- Capability Runtime
- Future Headmaster
- Specialist Agents
- REST API
- GUI
- Automated background workers

These components all require access to the same business logic.

Duplicating logic between CLIs, workflows, APIs, and agents would increase
maintenance cost and introduce inconsistent behavior.

---

# Decision

The Knowledge Engine shall adopt a strict layered architecture.

```
CLI
    ↓
Workflow
    ↓
Capability
    ↓
Service
    ↓
Implementation
    ↓
Storage
```

Each layer has a single responsibility.

---

# Layer Responsibilities


> **Legacy ADR**
>
> This ADR was created before the JARVIS ADR governance policy was established.
>
> Duplicate ADR numbers from this era are preserved intentionally for historical continuity.
>
> Beginning with **ADR-0017**, all Architecture Decision Records use unique,
> immutable numbering.

## 1. CLI

Purpose:

Human-facing command line interface.

Responsibilities:

- Parse command line arguments
- Construct execution context
- Call a Capability
- Display results

The CLI SHALL NOT contain business logic.

---

## 2. Workflow

Purpose:

Coordinate multiple capabilities.

Responsibilities:

- Determine execution order
- Resolve dependencies
- Track progress
- Handle cancellation
- Resume execution
- Aggregate results

A Workflow SHALL NOT access storage directly.

A Workflow SHALL NOT implement business logic.

---

## 3. Capability

Purpose:

Provide one reusable operation.

Examples:

- DiscoveryCapability
- ObjectCapability
- RegistryCapability
- LibrarianCapability
- GraphCapability

Responsibilities:

- Validate context
- Call one or more Services
- Produce metrics
- Return CapabilityResult

Capabilities SHALL NOT perform SQL directly.

Capabilities SHALL NOT duplicate implementation logic.

---

## 4. Service

Purpose:

Thin object-oriented wrapper around implementation modules.

Responsibilities:

- Call production implementation
- Normalize arguments
- Normalize return values

Services SHALL remain lightweight.

Services SHALL NOT duplicate algorithms.

---

## 5. Implementation

Purpose:

Contain production business logic.

Examples:

discover()

build_objects()

build_registry()

build_graph()

Implementation modules are considered the canonical source of behavior.

They may evolve internally but remain the public API consumed by Services.

---

## 6. Storage

Purpose:

Persistence.

Examples:

SQLite

FAISS

Filesystem

Future Graph Database

Storage SHALL contain no business logic.

---

# Allowed Dependencies

```
CLI
    ↓

Workflow
    ↓

Capability
    ↓

Service
    ↓

Implementation
    ↓

Storage
```

No layer may bypass the layer immediately beneath it.

---

# Forbidden Dependencies

Workflow → SQLite

Workflow → builder.py

Capability → SQLite

Capability → builder.py

CLI → builder.py

CLI → SQLite

Service → CLI

Implementation → Workflow

Implementation → Capability

---

# Migration Strategy

Existing implementation modules SHALL remain the canonical implementation.

Examples:

```
discover()

build_objects()

build_registry()

build_graph()

build_embeddings()
```

Migration consists of adding:

Service

↓

Capability

↓

Workflow registration

No implementation module should be rewritten solely to satisfy the layered
architecture.

---

# Benefits

Single implementation path

No duplicated business logic

Reusable by:

- CLI
- REST API
- Headmaster
- Specialists
- Background workers
- GUI
- Tests

Improved testability

Improved dependency management

Improved maintainability

Supports checkpointing

Supports parallel workflows

Supports future distributed execution

---

# Consequences

The Knowledge Engine becomes execution-environment independent.

Every subsystem exposes the same public execution model.

Future features such as:

- Headmaster orchestration
- Specialist agents
- Scheduled workflows
- Distributed processing
- Remote execution

can all reuse existing Capabilities without modifying implementation modules.

---

# Long-Term Vision

The layered architecture transforms the Knowledge Engine from a collection of
utilities into a reusable execution platform.

Every future subsystem shall follow this architecture by default.

The Workflow Engine becomes responsible for orchestration.

Capabilities become reusable building blocks.

Services become stable integration boundaries.

Implementation modules remain the canonical source of production logic.

This architecture establishes the foundation for the autonomous JARVIS
Headmaster, specialist agents, and future distributed knowledge processing.

# JARVIS Gen 2 — Phase VI-F3

# Runner Composition Contracts

**Status:** Complete

---

# Purpose

Phase VI-F3 establishes permanent architectural contracts for the
Assimilation Runner.

Following the service extraction milestones (VI-E1 through VI-E4), the
Runner has become a pure orchestration component. This phase freezes that
architecture by verifying its composition, dependency injection, public
interface, and immutable contracts.

The objective is to ensure that future development cannot silently move
business logic back into the Runner without breaking automated verification.

---

# Motivation

Earlier phases extracted the Runner's responsibilities into dedicated
services:

- AssimilationStateService
- DocumentPersistenceService
- AttemptJournalService
- ExtractionService

Although those responsibilities had been separated, nothing prevented a
future modification from bypassing those services or introducing new
business logic directly into the Runner.

Phase VI-F3 converts these architectural decisions into executable
contracts.

---

# Architectural Position

The Runner now serves exclusively as the orchestration layer.

```text
                     Director
                         │
                         ▼
               AssimilationRunner
                         │
     ┌──────────┬────────┼──────────┬──────────┐
     ▼          ▼        ▼          ▼
 State      Persistence Attempt  Extraction
 Service      Service    Service    Service
```

The Runner coordinates work.

It does not own business logic.

---

# Responsibilities

The AssimilationRunner owns:

- workflow orchestration
- transaction coordination
- service composition
- success and failure routing
- execution sequencing

The Runner does **not** own:

- lifecycle transitions
- document persistence
- attempt journaling
- document extraction
- checksum generation
- chunk generation
- registry SQL
- queue SQL

---

# Constructor Contract

The constructor forms part of the public architecture.

Required constructor parameters:

```text
db
default_max_attempts
state_service
persistence_service
attempt_service
extraction_service
```

Future modifications that alter constructor ordering, names, or dependency
injection behavior require an intentional architecture change and updated
verification.

---

# Dependency Injection Contract

The Runner supports dependency injection for every collaborating service.

Supported injected dependencies:

- AssimilationStateService
- DocumentPersistenceService
- AttemptJournalService
- ExtractionService

Injected objects must be preserved without replacement.

The Runner may construct default service instances only when a dependency
is not supplied.

---

# Default Composition

When no services are injected, the Runner shall construct default instances
of every required service.

Each Runner instance receives an independent service graph.

Construction must not:

- open database transactions
- modify registry state
- perform extraction
- persist documents
- journal attempts

Construction must remain side-effect free.

---

# Public API Contract

The Runner exposes only its orchestration interface.

Public methods:

- run_one_single_document()
- recover_stale_processing()
- requeue_failed_documents()

Helper methods remain private implementation details.

The public orchestration surface is intentionally small and stable.

---

# Handler Identity

The Runner permanently identifies itself as:

```text
document_assimilation
```

The handler identity participates in higher-level orchestration and must
remain stable unless the overall architecture changes.

---

# Retry Policy

The Runner validates retry configuration during construction.

Invariant:

```text
default_max_attempts >= 1
```

Invalid values must raise ValueError.

Silent correction is prohibited.

---

# ClaimedDocument Contract

ClaimedDocument is an immutable value object.

Fields:

- object_uuid
- object_path
- object_type
- attempt_number
- max_attempts
- attempt_id

Mutation after construction is prohibited.

The object represents a single claimed work item whose identity remains
constant throughout processing.

---

# Architectural Guarantees

Phase VI-F3 guarantees that:

✓ Runner remains an orchestration component.

✓ All business logic remains delegated.

✓ Service boundaries remain explicit.

✓ Dependency injection remains stable.

✓ Constructor behavior remains deterministic.

✓ Public API remains intentionally small.

✓ Immutable contracts remain enforced.

✓ Future refactoring cannot silently violate these rules.

---

# Verification

Focused verification:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_phase_6f3.sh
```

Master verification:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_all.sh
```

The focused verification confirms:

- handler identity
- constructor signature
- retry validation
- dependency injection
- default composition
- public API
- immutable ClaimedDocument contract

---

# Exit Criteria

Phase VI-F3 is complete when:

- Runner composition contracts are verified.
- Constructor contracts are frozen.
- Dependency injection is verified.
- Default composition is verified.
- Retry validation passes.
- Public API verification passes.
- ClaimedDocument immutability is verified.
- Focused verification succeeds.
- Master verification succeeds.
- Documentation is completed.
- The milestone is committed as a single historical unit.
- Changes are pushed to GitHub.

---

# Historical Notes

Phase VI-F3 completes the architectural stabilization of the
AssimilationRunner.

Previous phases transformed the Runner from a component that directly
performed extraction, persistence, lifecycle management, and attempt
tracking into a coordinator that delegates those responsibilities to
specialized services.

This phase preserves that design through automated architectural
verification.

Future capabilities—including distributed execution, parallel
assimilation, additional document formats, specialized extraction
pipelines, and higher-level orchestration by the Executive Director—can be
introduced without expanding the Runner's responsibilities.

From this point forward, the Runner should evolve primarily by composing
new services rather than by acquiring additional implementation logic.

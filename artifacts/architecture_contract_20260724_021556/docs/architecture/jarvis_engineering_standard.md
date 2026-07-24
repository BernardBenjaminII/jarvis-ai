# JARVIS Engineering Standard

## Version

1.0

## Status

Canonical after completion of JARVIS Gen 2 Phase VI-F6.

---

## Purpose

This standard defines the permanent engineering gates for JARVIS development.

A capability is not complete merely because it functions. It must preserve
architecture, expose stable interfaces, remain testable, produce explainable
results, and leave a focused historical milestone.

---

## Primary principle

> Prefer extension over modification.

New capabilities should plug into stable registries, handlers, repositories,
services, providers, directors, and mission interfaces.

Changes to frozen core components require an explicit migration plan, contract
updates, documentation updates, and full regression verification.

---

## Gate 0 — Historical audit

Before starting a phase:

1. Search Git history for the proposed files.
2. Confirm the milestone has not already been implemented.
3. Inspect the current branch and working tree.
4. Identify unrelated work that must remain unstaged.
5. Confirm the preceding milestone is committed and pushed.

Git history is the source of truth.

---

## Gate 1 — Responsibility

Every module must have one clear responsibility.

Canonical examples:

- Directors schedule and coordinate.
- Registries resolve implementations.
- Handlers own object-type behavior.
- Runners coordinate transactional workflows.
- Services own focused business operations.
- Repositories own persistence access and record mapping.
- Providers own external-system access.
- Models describe immutable data contracts.

A module must not absorb responsibilities already assigned to another layer.

---

## Gate 2 — Dependency direction

Dependencies point downward through the architecture.

Canonical direction:

```text
Executive
    ↓
Director
    ↓
Registry / Composition Root
    ↓
Handler
    ↓
Runner / Workflow Coordinator
    ↓
Service
    ↓
Repository / Provider
    ↓
Storage or External System

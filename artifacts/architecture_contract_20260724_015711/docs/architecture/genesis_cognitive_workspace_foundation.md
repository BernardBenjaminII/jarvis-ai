# Genesis III-A1 — Cognitive Workspace Foundation

## Purpose

The cognitive workspace is JARVIS's explicit, auditable working state for one
reasoning objective.

It prevents active reasoning from existing only as transient model context.
Instead, hypotheses, evidence, assumptions, questions, confidence changes, and
workspace status become first-class domain objects.

## Core invariant

> JARVIS must not silently reason over hidden mutable state.

Every meaningful cognitive transition produces:

- a new immutable workspace revision;
- an append-only event;
- a reproducible snapshot;
- an explicit identity for the affected object.

## Scope

Genesis III-A1 introduces:

- immutable workspace contracts;
- explicit hypotheses;
- canonical evidence references;
- explicit assumptions;
- unresolved and resolved questions;
- hypothesis confidence and status transitions;
- workspace lifecycle states;
- append-only cognitive events;
- deterministic snapshots;
- a service layer for valid state transitions.

## Non-goals

This phase does not yet provide:

- persistence;
- concurrency control;
- reasoning-engine orchestration;
- automatic hypothesis generation;
- contradiction detection;
- confidence propagation;
- UI integration;
- cross-session recovery.

Those capabilities build on this foundation.

## Lifecycle

A workspace begins in `open` status.

It may transition to:

- `suspended`;
- `resolved`;
- `abandoned`.

Resolved and abandoned workspaces are terminal.

## Revision model

All service operations return a new workspace object.

The previous workspace remains unchanged.

Each successful operation increments the workspace revision and records an event.

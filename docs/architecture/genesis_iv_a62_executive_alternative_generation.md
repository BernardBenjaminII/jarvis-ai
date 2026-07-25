# Genesis IV-A6.2 — Executive Alternative Generation

## Purpose

IV-A6.2 converts a certified IV-A5 executive reasoning result into a bounded set of immutable, deterministic **Courses of Action (COAs)**. It sits before IV-A6.1 decision synthesis and does not create missions, objectives, executable tasks, commands, or operations.

## Boundary

`reasoning -> COA generation -> decision synthesis -> executive planning -> operations`

The canonical owner is `core.cognition.coa`. Executive planning remains owned by `core.executive.planning`; execution remains owned by `core.operations`.

## Guarantees

- structural compatibility with IV-A5 reasoning results;
- deterministic identities and ranking;
- bounded candidate count;
- mandatory hold and contingency alternatives under default policy;
- immutable contracts and idempotent repository behavior;
- neutral adapter data for IV-A6.1 without importing or duplicating decision contracts.

## Deliberate exclusions

No mission compilation, task scheduling, resource reservation, authorization, command dispatch, or side effects are permitted in this phase.

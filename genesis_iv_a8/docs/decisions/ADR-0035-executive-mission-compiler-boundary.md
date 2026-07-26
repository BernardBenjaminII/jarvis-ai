# ADR-0035 — Executive Mission Compiler Boundary

**Status:** Accepted  
**Milestone:** Genesis IV-A8

## Context

Genesis IV-A7 selects a constitutionally admissible Course of Action. The
Executive requires a separate boundary that converts the approved decision into
structured work without executing that work.

## Decision

Create `core.cognition.mission_compiler` as the canonical owner of deterministic
mission compilation.

The compiler shall:

- accept only approved Executive Decisions;
- produce immutable mission planning artifacts;
- preserve decision and cognition traceability;
- validate parent-child relationships;
- produce a directed acyclic execution graph;
- reject cycles and orphaned nodes;
- assign deterministic identifiers; and
- remain isolated from execution dispatch.

## Consequences

Planning becomes inspectable, serializable, reproducible, and certifiable.
Execution systems may consume the Mission Plan but may not rewrite its recorded
decision lineage.

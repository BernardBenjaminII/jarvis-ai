# Cognitive Architecture Convergence

This directory records the controlled reconciliation of JARVIS cognitive
architecture and implementation.

## Purpose

JARVIS currently contains multiple generations of Executive and planning
code, together with an expanded constitutional, architectural, specification,
standards, and whitepaper corpus.

The convergence phases prevent destructive cleanup and architectural drift.

## Phase structure

### IX-C1 — Inventory and Preservation

- Preserve the existing workspace.
- Inventory competing implementations.
- Record public symbols and imports.
- Record source hashes.
- Detect duplicate public names.
- Compare root-level whitepapers with canonical documentation locations.
- Make no destructive source changes.

### IX-C2 — Canonical Ownership

- Assign canonical ownership to planning components.
- Define the stable Planning Engine public interface.
- Determine the role of legacy `planner.py`.
- Determine whether `planning_engine/` contributes contracts or should be
  superseded.
- Define compatibility boundaries.

### IX-C3 — Controlled Migration

- Move reusable implementation into canonical packages.
- Add compatibility imports where necessary.
- Update Executive orchestration.
- Update tests and verification.
- Remove obsolete code only after regression verification.

### IX-C4 — Architecture Freeze

- Freeze canonical cognitive subsystem boundaries.
- Record architectural fingerprints.
- Update subsystem ownership documentation.
- Permit Reasoning Engine implementation to begin.

## Governing rule

No file is deleted merely because another file has a similar name.

Deletion requires:

1. content comparison;
2. ownership determination;
3. dependency analysis;
4. migration or compatibility coverage;
5. regression verification;
6. recorded architectural justification.

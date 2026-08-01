# Genesis VII-C4.3 Pack 3B-2B.2 — Directorate Projection

## Mission

Assign every repository ownership domain from Pack 3B-2B.1 to a canonical directorate and expose the result through deterministic graph, query, metric, and reporting layers.

## Assignment policy

Ownership assignment uses ordered, deterministic path-prefix rules.

High-specificity rules take precedence over broad engineering ownership.

Examples:

- `core/governance` → Governance Directorate
- `core/knowledge` → Knowledge Directorate
- `core/reasoning` → Reasoning Directorate
- `core/planning` → Planning Directorate
- `core/operations` → Operations Directorate
- `core/acquisition` → Intelligence Acquisition Directorate
- `tests`, `dev`, `scripts`, and unmatched `core` domains → Software Engineering Directorate
- executive documentation and executive packages → Executive Directorate

## Relationships materialized

- `owns`
- `maintains`

The foundation relationships remain preserved:

- `supervises`
- `responsible_for`

## Query surface

The projection answers:

- list canonical directorates;
- list responsibilities;
- list ownership domains;
- show domains owned by a directorate;
- show domains maintained by a directorate;
- show responsibilities of a directorate;
- identify the owner of an ownership domain;
- show unowned domains.

## Metrics

- ownership domains;
- owned domains;
- unowned domains;
- ownership completeness;
- ownership distribution by directorate;
- node and edge distributions.

## Canonical artifacts

`artifacts/audit/km0000-c4_3-pack3b2b2/`

- `constitutional_directorate_projection.json`
- `constitutional_directorate_nodes.json`
- `constitutional_directorate_edges.json`
- `constitutional_directorate_metrics.json`
- `constitutional_directorate_integrity.json`
- `constitutional_directorate_summary.md`

## Boundary

Pack 3B-2B.2 completes ownership projection and executive queries.

Pack 3B-2B.3 should consolidate the final public API, certification surface, compatibility checks, and complete Pack 3B-2B integration contract.

## Revision A correction

The test fixture now models a complete certified Pack 3B-2B.1 foundation. Canonical completeness validation remains strict and is not bypassed.

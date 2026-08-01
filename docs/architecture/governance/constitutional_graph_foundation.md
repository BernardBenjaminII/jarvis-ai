# Genesis VII-C4.3 Pack 3A — Constitutional Graph Foundation

## Mission

Establish the deterministic graph substrate required to represent and traverse constitutional authority across the JARVIS repository.

Pack 3A converts the certified Pack 2 article-usage registry into canonical nodes and edges. It does not yet infer directorates, capabilities, ADR relationships, or higher-order organizational dependencies. Those belong to Packs 3B and 3C.

## Source

Pack 3A consumes:

`artifacts/audit/km0000-c4_3-pack2/constitutional_article_usage.json`

The Pack 2 article-intelligence fingerprint is preserved as the immediate upstream authority.

## Canonical node types

- `article`
- `repository_artifact`
- `domain`

## Canonical edge types

- `governs`
- `observed_in_domain`
- `belongs_to_domain`

The `belongs_to_domain` edge is emitted only when a Pack 2 article observation identifies exactly one domain. It is explicitly marked as an inference.

## Determinism

Nodes and edges use stable identifiers, canonical ordering, canonical JSON serialization, and SHA-256 fingerprints derived from normalized content.

## Integrity rules

Pack 3A rejects or diagnoses:

- duplicate node identifiers;
- duplicate edge identifiers;
- dangling edges;
- unexpected self-loops.

Unused constitutional articles remain valid isolated nodes. They are not treated as graph corruption because their isolation accurately represents the certified coverage baseline.

## Query substrate

The foundation graph supports:

- node lookup;
- incoming-edge lookup;
- outgoing-edge lookup;
- neighbor lookup;
- deterministic forward reachability.

## Canonical artifacts

Output directory:

`artifacts/audit/km0000-c4_3-pack3a/`

Files:

- `constitutional_graph_foundation.json`
- `constitutional_graph_nodes.json`
- `constitutional_graph_edges.json`
- `constitutional_graph_metrics.json`
- `constitutional_graph_integrity.json`
- `constitutional_graph_foundation_report.md`

## Boundary

Pack 3A establishes graph contracts and infrastructure. Pack 3B will add authority, repository, directorate, capability, ADR, and architectural graph projections. Pack 3C will add traceability matrices, advanced traversal, impact analysis, and executive explanations.

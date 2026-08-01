# Genesis VII-C4.3 Pack 3B-2A — Constitutional Repository Projection

## Mission

Project the Pack 3B-1 authority graph into a deterministic semantic model of the JARVIS repository.

## Upstream chain

The projection consumes:

`artifacts/audit/km0000-c4_3-pack3b1/constitutional_authority_graph.json`

It preserves the Pack 2 article-intelligence fingerprint, Pack 3A graph-foundation fingerprint, and Pack 3B-1 authority-graph fingerprint.

## Node kinds

`repository`, `package`, `module`, `document`, `test`, `verification`, `configuration`, `executable`, `data_artifact`, and `unknown`.

## Deterministic classification

Repository paths are normalized and classified by stable rules. Intermediate directories become synthetic package nodes so that every projected artifact belongs to one rooted containment hierarchy.

## Integrity

The projection requires one repository root, unique node and edge identifiers, no dangling edges, valid containment semantics, and no orphan non-root nodes.

## Metrics

Pack 3B-2A reports counts by node kind, containment edges, classified and unclassified nodes, and classification completeness.

## Query surface

The query service exposes packages, modules, tests, verification artifacts, children, recursive descendants, artifacts under a path, and unknown artifacts.

## Canonical output

`artifacts/audit/km0000-c4_3-pack3b2a/`

- `constitutional_repository_projection.json`
- `constitutional_repository_nodes.json`
- `constitutional_repository_edges.json`
- `constitutional_repository_metrics.json`
- `constitutional_repository_integrity.json`
- `constitutional_repository_summary.md`

## Boundary

Pack 3B-2A establishes repository semantics. Pack 3B-2B should establish directorate projection. Pack 3B-2C should establish capability projection and ownership relationships.

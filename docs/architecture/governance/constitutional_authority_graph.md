# Genesis VII-C4.3 Pack 3B-1 — Constitutional Authority Graph

## Mission

Project the Pack 3A structural graph into a deterministic semantic authority graph that distinguishes constitutional articles, governed artifacts, governance domains, authority classes, and authorization relationships.

Pack 3B-1 is the first semantic projection over the constitutional graph foundation.

## Upstream authority

Pack 3B-1 consumes:

`artifacts/audit/km0000-c4_3-pack3a/constitutional_graph_foundation.json`

It preserves both:

- the Pack 3A graph-foundation fingerprint;
- the Pack 2 article-intelligence fingerprint carried by Pack 3A.

## Node kinds

- `constitutional_article`
- `authority_class`
- `governed_artifact`
- `governance_domain`

## Authority classes

- `critical`
- `review`
- `active`
- `cold`
- `unknown`

Pack 3A article classifications are normalized as follows:

- `exercised` → `active`
- `underutilized` → `review`
- `unused` → `cold`
- hotspot labels map to their equivalent authority class
- unknown values remain explicit as `unknown`

## Edge kinds

- `classified_as`
- `authorizes`
- `exercised_in`
- `supports_authority_class`

The `authorizes` edge is the semantic projection of Pack 3A's structural `governs` edge.

## Integrity rules

An authorization edge is valid only when:

- its source is a constitutional article;
- its target is a governed artifact;
- both endpoints exist in the authority graph.

Duplicate identifiers and dangling edges are prohibited.

## Metrics

Pack 3B-1 computes:

- article count;
- governed-artifact count;
- governance-domain count;
- authorization edge count;
- authority-class distribution;
- exercised and unexercised article counts;
- authority-utilization ratio.

## Query surface

The authority query service supports:

- governed artifacts for an article;
- governing articles for an artifact;
- articles by authority class;
- unexercised constitutional articles.

## Canonical artifacts

Output directory:

`artifacts/audit/km0000-c4_3-pack3b1/`

Files:

- `constitutional_authority_graph.json`
- `constitutional_authority_nodes.json`
- `constitutional_authority_edges.json`
- `constitutional_authority_metrics.json`
- `constitutional_authority_integrity.json`
- `constitutional_authority_summary.md`

## Boundary

Pack 3B-1 establishes constitutional authority semantics. Pack 3B-2 will add repository, directorate, and capability projections. Pack 3B-3 will add ADR projection, cross-projection queries, reporting, and final Pack 3B certification.

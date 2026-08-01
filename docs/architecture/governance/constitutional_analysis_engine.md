# Genesis VII-C2 — Constitutional Analysis Engine

## Mission

Transform the deterministic claim corpus produced by Genesis VII-C1 into a deterministic constitutional relationship graph.

## Inputs

The engine consumes the canonical VII-C1 artifacts:

- `artifacts/audit/km0000-c1/constitutional_extraction.json`
- `artifacts/audit/km0000-c1/constitutional_claims.json`

## Outputs

The canonical output directory is:

`artifacts/audit/km0000-c2/`

Artifacts:

- `constitutional_analysis.json`
- `constitutional_graph.json`
- `constitutional_conflicts.json`
- `constitutional_duplicates.json`
- `constitutional_concordance.json`
- `constitutional_authority.json`
- `constitutional_analysis_report.md`

## Deterministic analysis

C2 uses deterministic text normalization, exact duplicate detection, bounded lexical similarity, normative polarity, domain matching, and document-authority ranking.

No model inference, network access, runtime imports, clocks, or random values are used.

## Authority hierarchy

1. Constitution
2. Engineering Constitution
3. Policy
4. ADR
5. Architecture
6. Whitepaper
7. Other

Authority resolution is advisory evidence for later ratification. C2 does not itself ratify, repeal, or rewrite doctrine.

## Relationship semantics

- `duplicates`: materially equivalent normalized statements.
- `supports`: concordant claims within the same domain.
- `contradicts`: high-overlap claims with opposite normative polarity.
- `refines`: a materially overlapping statement adds detail.
- Additional relationship types are reserved by the public contract for future certified revisions.

## Boundary

C2 identifies candidate relationships. Human or later constitutionally authorized machinery must adjudicate semantic ambiguity and ratify canonical doctrine.

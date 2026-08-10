# Genesis X-B2.4A — Synthesis Quality Hardening

## Purpose

Improve the answer utility of already-qualified Genesis X-B2.3 evidence
without modifying retrieval, semantic vectors, corpus state, or provenance.

## Pipeline

B2.1 Vector Search
→ B2.2 Hybrid Retrieval
→ B2.3 Evidence Context Assembly
→ B2.4A Evidence Focus / Utility Ranking
→ B2.4 Qualification Adapter
→ GroundedAnswerEngine

## Invariants

1. No semantic database writes.
2. No runtime catalog writes.
3. No embedding mutation.
4. No evidence is fabricated.
5. No evidence is added beyond the B2.3 selected set.
6. Provenance identifiers remain unchanged.
7. Citation contracts remain owned by GroundedAnswerEngine.
8. Uncertainty and conflict contracts remain unchanged.
9. Evidence focusing is deterministic.
10. Ranking is query-conditioned rather than domain-specific.

## Scope

B2.4A changes synthesis-facing evidence ordering and passage focus only.
It is not a replacement retrieval engine and is not an LLM generation layer.

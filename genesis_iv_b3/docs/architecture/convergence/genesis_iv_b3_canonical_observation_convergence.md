# Genesis IV-B3 — Canonical Observation Convergence
## Mission
Genesis IV-B3 is the first true Convergence Phase. It unifies every Observation producer, contract, consumer, and transport under one standard without destructively rewriting certified legacy subsystems.

## Existing halves
```text
Cognition Extraction Engine:
Extraction → Candidate → Normalization → Confidence → Observation

Executive Observation Bus:
Observation → Repository → Publication → Subscribers
```
These are complementary. The extraction engine creates facts from sources—including books and files. The bus persists and transports them.

## Canonical flow
```text
Live Reality ───────┐
Recorded Reality ───┼→ Producers/Extractors → Legacy Adapters
Executive Reality ──┤                         ↓
Human Reality ──────┘              core.observation.Observation
                                           ↓
                         Bus / Snapshot / Evidence / Situation
```

## Ownership
`core.observation` owns the immutable contract, provenance, enums, serialization, adapters, and convergence audit. It does not own extraction, persistence, transport, evidence, reasoning, decision, execution, or UI state.

## Recorded Reality
Books, PDFs, files, source code, images, transcripts, databases, and archives are first-class sources. A document-derived statement remains an observation until the Evidence domain admits and assesses it.

## Migration
1. Ratify the canonical owner.
2. Adapt legacy shapes.
3. Verify consumers.
4. Migrate producers incrementally.
5. Deprecate duplicates only after downstream certification.
6. Preserve history for audit.

No certified legacy implementation is deleted by IV-B3.

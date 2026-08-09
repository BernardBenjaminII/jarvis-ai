# Genesis IX-A4.5 Pack 1A — Runtime Interface

Defines immutable canonical contracts between retrieval and grounding without changing runtime behavior.

## Contracts

- `EvidenceCandidate`
- `QualificationScore`
- `QualificationDecision`
- `QualifiedEvidence`
- `QualificationResult`

## Guarantees

- defensive metadata copying;
- normalized score range `[0.0, 1.0]`;
- stable enum values;
- stable JSON serialization;
- explicit accepted and rejected partitions;
- no changes to retrieval, grounding, awareness, Director, or conversation behavior.

# Genesis IV-A2 — Evidence Association Architecture

## Status

Implementation in progress.

Part 1 establishes the evidence constitution and immutable contracts.

## Purpose

Genesis IV-A2 introduces the permanent evidence layer between direct
observations and higher cognition.

The evidence layer answers:

- What supports an observation?
- What opposes it?
- Where did the evidence originate?
- How was it acquired?
- Can the evidence be reproduced and audited?
- Is the evidence chain contested or incomplete?

## Pipeline

```text
Represented Knowledge
        ↓
Observation
        ↓
Provenance Record
        ↓
Evidence Record
        ↓
Evidence Chain
        ↓
Claim Extraction
        ↓
Relationship Discovery
        ↓
Hypothesis Construction
        ↓
Interpretation
Constitutional Objects
ProvenanceRecord

A provenance record identifies:

the source reference;
provenance classification;
acquisition method;
source system or actor;
parent provenance records;
immutable metadata.

Provenance records do not declare truth.

EvidenceRecord

An evidence record associates:

one or more observations;
one provenance record;
an evidence classification;
a direction;
a quality rating;
confidence in the evidence record;
optional description and metadata.

Evidence direction is explicit:

supports;
opposes;
neutral.
EvidenceChain

An evidence chain groups evidence around a cognitive subject.

The subject may later be:

an observation;
a claim;
a relationship;
a hypothesis;
an interpretation.

Evidence chains preserve supporting and opposing material rather than erasing
disagreement.

Determinism

Every Genesis IV-A2 object has a deterministic identifier derived from its
canonical constitutional content.

Equivalent objects must produce identical identifiers regardless of input
ordering.

Separation of Concerns

The evidence layer does not:

infer claims;
decide which interpretation is correct;
generate plans;
execute actions;
suppress contradicting evidence.

Association policy belongs to the Part 2 association engine.

Phase Deliveries
Part 1 — Evidence Foundation
provenance contracts;
evidence contracts;
evidence-chain contracts;
deterministic identifiers;
validation;
public exports;
architectural documentation.
Part 2 — Association Engine
deterministic association rules;
candidate association;
evidence deduplication;
source and observation matching;
chain construction;
contested-chain detection.
Part 3 — Certification
unit tests;
verifier;
regression suite;
integration checks;
architecture fingerprint;
final phase documentation.

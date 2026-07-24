# Genesis IV-A3 — Claim Construction Architecture

## Status

Implemented.

## Purpose

Genesis IV-A3 introduces immutable, evidence-grounded claims.

A claim is a normalized proposition constructed from:

- one observation;
- one validated evidence chain;
- explicit claim classification;
- deterministic status policy;
- explicit confidence;
- complete provenance through the evidence chain.

## Pipeline

```text
Observation
    ↓
Evidence Record
    ↓
Evidence Chain
    ↓
Claim Candidate
    ↓
Claim Construction Policy
    ↓
Immutable Claim Record
Claim Structure

A claim contains:

a canonical subject;
a canonical predicate;
an object value or object reference;
a claim kind;
polarity;
status;
scope;
confidence;
observation references;
a complete evidence chain;
deterministic identity.
Claim Statuses
Proposed

Evidence exists, but the configured support or opposition threshold has not
been met.

Supported

Supporting evidence exists and the evidence-chain confidence meets the
configured threshold.

Contested

Supporting and opposing evidence coexist.

Insufficient

The evidence chain lacks sufficient directional or quantitative evidence.

Rejected

Opposing evidence exists and the configured rejection threshold is met.

Constitutional Boundary

Claim construction does not:

create evidence;
discover evidence chains;
infer hidden causes;
resolve contradictions;
construct hypotheses;
interpret strategic meaning;
create plans;
execute actions.
A2 Dependency

The current A3 implementation accepts validated evidence chains directly.

Genesis IV-A2's later automatic association engine will produce these chains
from observation collections. The boundary is intentional:

A2: Which evidence belongs together?
A3: What proposition does that evidence support or oppose?
Determinism

Equivalent observations, evidence chains, policies, and metadata produce
identical claim identifiers.

Input ordering does not alter canonical identity.

Future Integration

Claims produced by A3 become inputs for:

Genesis IV-A4 relationship discovery;
Genesis IV-B hypothesis construction;
Genesis IV-C interpretation;
reasoning justification;
executive decision auditing.

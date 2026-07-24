# ADR-0019: Genesis IV Claim Constitution

**Status:** Accepted  
**Phase:** Genesis IV-A3  
**Decision scope:** Cognition architecture

## Context

Observations describe extracted facts or states. Evidence records describe
source-grounded support, opposition, and context. Neither object should be
treated automatically as a proposition suitable for reasoning.

JARVIS requires a permanent claim layer between evidence and higher-order
reasoning.

## Decision

JARVIS shall represent claims as immutable, deterministically identified,
evidence-grounded cognitive objects.

Claims shall use a normalized subject-predicate-object representation.

Every claim shall retain:

- its originating observation identifiers;
- its complete evidence chain;
- explicit polarity;
- explicit status;
- explicit scope;
- evidence-derived confidence.

## Constitutional Rules

1. Every claim must reference at least one observation.
2. Every claim must contain a validated evidence chain.
3. Referenced observations must occur in that evidence chain.
4. Claim identity must be deterministic.
5. Input ordering must not alter claim identity.
6. Contradictory evidence must remain visible.
7. A contested claim must retain supporting and opposing evidence.
8. A supported claim must contain supporting evidence.
9. A rejected claim must contain opposing evidence.
10. Claim construction must not create missing evidence.
11. Claim construction must not perform hypothesis generation.
12. Claim construction must not perform interpretation.
13. Claim confidence must remain separate from truth certainty.
14. Claims must be immutable after construction.

## Consequences

### Positive

- propositions become auditable;
- evidence remains attached to reasoning inputs;
- contradictions are represented explicitly;
- later hypothesis generation receives normalized propositions;
- deterministic identities support deduplication and persistence.

### Costs

- claim and evidence lifecycles must be maintained separately;
- evidence-chain quality directly constrains claim quality;
- contested propositions cannot be silently resolved;
- automatic evidence association remains a separate subsystem.

## Rejected Alternatives

### Treat observations as claims

Rejected because observations describe extracted content without determining
the proposition's evidence status.

### Treat evidence records as claims

Rejected because evidence describes support or opposition, not the normalized
proposition itself.

### Resolve contradiction during claim construction

Rejected because contradiction resolution belongs to later reasoning and
interpretation layers.

### Generate random claim identifiers

Rejected because equivalent cognitive objects must converge to stable
identities.

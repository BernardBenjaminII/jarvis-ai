
ADR-0018: Genesis IV Evidence Constitution

Status: Accepted
Decision scope: Genesis IV cognition architecture
Phase: Genesis IV-A2

Context

Reasoning directly over unstructured knowledge weakens traceability. A
conclusion may appear plausible without preserving an auditable path to the
material that supports or opposes it.

JARVIS requires a first-class evidence layer that remains separate from claims,
hypotheses, interpretations, plans, and executive actions.

Decision

JARVIS shall represent provenance, evidence, and evidence chains as immutable,
deterministically identified cognitive objects.

Evidence shall explicitly identify whether it supports, opposes, or remains
neutral toward its associated cognitive subject.

Contradicting evidence shall be retained.

Evidence confidence shall describe evidence quality and traceability rather
than the ultimate truth of a conclusion.

Constitutional Rules
Evidence must have provenance.
Provenance must resolve to a source reference.
Evidence must reference at least one observation.
Evidence direction must be explicit.
Supporting and opposing evidence may coexist.
Evidence chains must preserve disagreement.
Identifiers must be deterministic.
Input ordering must not alter canonical identity.
Evidence objects must be immutable.
Evidence association must not perform interpretation.
Missing evidence must not be silently fabricated.
Later cognition must be able to audit its complete evidence chain.
Consequences
Positive
conclusions become auditable;
contradictory sources remain visible;
evidence can be reused across claims;
reasoning can distinguish direct evidence from inference;
evidence chains can be inspected independently of final decisions.
Costs
additional cognitive objects must be stored;
association policies require careful deterministic rules;
evidence quality and conclusion confidence remain separate concepts;
unresolved conflicts must be represented rather than hidden.
Rejected Alternatives
Attach source identifiers directly to claims

Rejected because this collapses observation, evidence, and inference into one
object.

Allow evidence without provenance

Rejected because unsupported evidence cannot be audited.

Remove contradicting evidence during normalization

Rejected because normalization must not decide truth.

Use random UUIDs

Rejected because equivalent cognitive objects must converge to stable
identifiers.

# Genesis VII-C4 — Constitutional Compliance Engine

## Mission

Evaluate proposed changes, architecture decisions, policies, plans, and other declared subjects against the ratified constitutional registry produced by Genesis VII-C3.

## Inputs

C4 consumes:

- `artifacts/audit/km0000-c3/constitutional_ratification.json`
- `artifacts/audit/km0000-c3/constitutional_registry.json`
- a deterministic compliance subject file

Canonical subject form:

```json
{
  "subjects": [
    {
      "subject_id": "SUBJECT-001",
      "subject_type": "proposal",
      "path": "docs/proposals/example.md",
      "title": "Example proposal",
      "content": "The proposal text to evaluate.",
      "domain": "governance"
    }
  ]
}
```

## Outputs

Canonical output directory:

`artifacts/audit/km0000-c4/`

Artifacts:

- `constitutional_compliance.json`
- `constitutional_compliance_subjects.json`
- `constitutional_compliance_findings.json`
- `constitutional_compliance_assessments.json`
- `constitutional_compliance_traceability.json`
- `constitutional_compliance_report.md`

## Deterministic evaluation

C4 uses:

- stable text normalization
- domain matching
- deterministic token overlap
- normative polarity comparison
- explicit thresholds
- stable ordering
- complete fingerprint chaining

C4 does not use:

- LLM inference
- embeddings
- random values
- network services
- wall-clock time

## Status semantics

- `compliant`: subject materially aligns with an applicable article.
- `review_required`: subject is relevant but requires human interpretation.
- `noncompliant`: subject materially contradicts an applicable article.
- `not_applicable`: no article meets the declared applicability threshold.

## Governance boundary

C4 produces candidate compliance findings. It does not replace Commander judgment, legal review, security review, or formal constitutional adjudication.

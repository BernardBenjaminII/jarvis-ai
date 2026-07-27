# Genesis VII-C1 — Constitutional Extraction Engine

**Status:** Implementation Candidate  
**Schema:** `1.0.0`  
**Dependency:** Genesis VII-C0 Pack 1B-R1

## Mission

Transform the certified repository inventory into deterministic, reviewable constitutional claim candidates while preserving exact repository provenance.

## Constitutional Principle

> The Constitution is discovered, not invented.

The engine does not ratify doctrine. It extracts candidate claims from repository evidence. Ratification remains a separate governance act.

## Inputs

- A `RepositoryInventory` produced by the certified C0 discovery engine.
- Repository Markdown source files classified as constitutional, architecture, or ADR documents.
- An immutable `ExtractionPolicy`.

## Outputs

`artifacts/audit/km0000-c1/` contains:

- `constitutional_extraction.json`
- `constitutional_claims.json`
- `constitutional_sources.json`
- `constitutional_extraction_report.md`

Every claim contains:

- Stable claim identifier.
- Source repository identifier.
- Source document identifier when declared.
- Original and normalized claim text.
- Normative modality.
- Inferred constitutional domain.
- Review status.
- File, line range, section path, and excerpt hash.
- Explicit rule-based confidence basis.

## Determinism

The engine uses no runtime imports, network access, language models, timestamps, randomness, or mutable global state. Identical certified repository evidence and policy produce identical extraction fingerprints.

## Boundaries

C1 does not:

- Ratify claims.
- Resolve contradictions.
- Rewrite repository doctrine.
- Infer unstated requirements.
- Assign executive authority.

Those responsibilities belong to later constitutional governance phases.

# Genesis VII-C4.2 — Repository-Wide Constitutional Audit

## Mission

Apply the ratified Constitution to every eligible governed artifact in the JARVIS repository and produce a deterministic, traceable constitutional health assessment.

## Default audit boundary

The initial release audits textual governance and engineering artifacts:

- Markdown and reStructuredText;
- plain text;
- JSON;
- YAML;
- TOML.

Source code is available through policy but disabled by default. This prevents the first repository-wide audit from treating implementation syntax as constitutional prose.

## Architecture

```text
Repository discovery
        ↓
Deterministic artifact inventory
        ↓
C4 compliance subjects
        ↓
Constitutional compliance evaluation
        ↓
Artifact assessments
        ↓
Article usage and heat map
        ↓
Canonical audit artifacts
```

C4.2 does not duplicate compliance logic. It delegates every artifact-to-article evaluation to the certified C4 engine.

## Exclusions

The default policy excludes:

- `.git`;
- migration backups;
- caches;
- virtual environments;
- build products;
- `node_modules`;
- existing audit artifacts.

## Fingerprint chain

```text
Repository
↓
Extraction
↓
Analysis
↓
Ratification
↓
Compliance
↓
Certification
↓
Repository Audit
```

## Canonical artifacts

Output directory:

`artifacts/audit/km0000-c4_2/`

Files:

- `constitutional_repository_inventory.json`
- `constitutional_repository_audit.json`
- `constitutional_repository_statistics.json`
- `constitutional_article_usage.json`
- `constitutional_article_heatmap.json`
- `constitutional_repository_traceability.json`
- `constitutional_repository_findings.json`
- `constitutional_repository_report.md`

## Interpretation

A `review_required` or `noncompliant` classification is an auditable finding, not an automatic declaration that the underlying artifact is invalid. Commander review remains authoritative.

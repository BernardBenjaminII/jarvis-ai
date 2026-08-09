# Genesis IX-A5 Pack 2 — Engineering Report Framework

## Mission

Establish one canonical report contract for Genesis audits, certifications,
verifications, migrations, and diagnostics.

## Contract

Every new engineering tool should return an `EngineeringReport` subclass with:

- `schema_version`;
- `kind`;
- `status`;
- `classification`;
- `title`;
- `summary`;
- `checks`;
- `warnings`;
- `recommendations`;
- `generated_at`;
- `metadata`;
- `to_dict()`;
- `to_json()`;
- `to_markdown()`;
- `write_json()`;
- `write_markdown()`.

## Report Types

```text
EngineeringReport
├── CertificationReport
├── AuditReport
├── VerificationReport
├── MigrationReport
└── DiagnosticsReport
```

## Compatibility Boundary

Historical tools may still return dictionaries. `normalize_report()` converts
legacy mappings and `to_dict()` objects into a canonical immutable
`EngineeringReport`.

New tools should return report objects directly. The compatibility adapter
exists to permit controlled migration, not permanent ambiguity.

## Immediate Repair

Pack 2 migrates the IX-A5 Pack 1 retrieval-audit runner so both of these are
accepted safely:

```python
KnowledgeSubstrateAudit.execute() -> dict
KnowledgeSubstrateAudit.execute() -> KnowledgeSubstrateReport
```

The runner normalizes either form before serialization, eliminating the
`dict has no attribute to_dict` failure while preserving the live audit logic.

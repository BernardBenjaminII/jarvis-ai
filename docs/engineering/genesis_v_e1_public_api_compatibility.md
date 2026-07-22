# Genesis V-E1 — Public API Compatibility Intelligence

## Mission

Give the Engineering OS a deterministic, read-only ability to:

- derive public API expectations from tests;
- inventory package exports without importing runtime modules;
- locate candidate implementations;
- classify compatibility regressions;
- recommend the smallest restoration;
- generate durable engineering evidence.

## Safety Model

V-E1 performs static AST analysis. It does not:

- import analyzed runtime packages;
- modify source;
- write Git state;
- apply recommendations;
- approve migrations;
- delete implementations.

Generated manifests and reports are engineering evidence, not autonomous authority.

## Workflow

```bash
python -m core.engineering.cli bootstrap-manifest
python -m core.engineering.cli analyze
```

The analyzer returns:

- exit code `0` when compatible;
- exit code `2` when restoration is required;
- exit code `1` for an execution failure.

An exit code of `2` is a successful analysis with compatibility findings.

## Produced Evidence

```text
dev/verification/manifests/test_public_api_expectations.json
.artifacts/engineering/public_api_compatibility.json
docs/audits/public_api_compatibility_report.md
```

## Next Step

A human reviews the report. Approved missing exports are then restored through
a separate Evolution Pack with regression verification and rollback evidence.

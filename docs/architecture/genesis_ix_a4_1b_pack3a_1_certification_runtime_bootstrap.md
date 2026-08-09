# Genesis IX-A4.1B Pack 3A.1 — Certification Runtime Bootstrap

## Mission

Provide one deterministic runtime bootstrap for all Genesis certification
programs.

## Responsibilities

- discover the repository root;
- add the repository root to `sys.path`;
- normalize `PYTHONPATH`;
- set `JARVIS_PROJECT_ROOT`;
- execute certification from the repository root;
- discover runtime, knowledge, and catalog locations;
- verify module resolution;
- verify the SQLite catalog;
- produce JSON and Markdown reports;
- repair Pack 3A before retrying certification.

## Canonical Usage

```python
from core.certification.runtime import CertificationRuntime

runtime = CertificationRuntime().bootstrap()
report = runtime.certify()
```

## Outputs

```text
docs/audits/certification_runtime/
    runtime_environment.md
    module_resolution.md
    repository_layout.md
    bootstrap_trace.md
    runtime_bootstrap.json
```

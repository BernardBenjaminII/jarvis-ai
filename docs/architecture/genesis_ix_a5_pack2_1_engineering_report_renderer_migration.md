# Genesis IX-A5 Pack 2.1 — Engineering Report Renderer Migration

## Mission

Eliminate legacy dictionary-coupled rendering and establish one canonical
renderer for Genesis engineering reports.

## Rendering Pipeline

```text
dict or legacy object
    ↓
normalize_report()
    ↓
EngineeringReport
    ↓
EngineeringReportRenderer
    ├── Markdown
    ├── JSON
    ├── Terminal
    └── Summary projection
```

## Canonical API

```python
EngineeringReportRenderer.render_markdown(report)
EngineeringReportRenderer.render_json(report)
EngineeringReportRenderer.render_terminal(report)
EngineeringReportRenderer.render_summary(report)
```

## Immediate Repair

Pack 2.1 migrates the IX-A5 Pack 1 retrieval-audit runner away from:

```python
render_markdown(data)
data["database"]["path"]
```

and onto the canonical report renderer.

The runner no longer needs to know the legacy raw-audit schema. Database,
retrieval, and qualification details remain inside the canonical report
summary and metadata.

## Compatibility

The renderer accepts either an `EngineeringReport` or a legacy mapping.
Normalization occurs once at the boundary, after which rendering is entirely
contract-driven.

## End State

After Pack 2.1, the reporting infrastructure is considered complete enough to
resume the knowledge-substrate investigation. Future audit work should focus on
catalog, chunk, FTS, retrieval, and qualification behavior rather than output
format repairs.

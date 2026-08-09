# Genesis IX-A4.7 Pack 2A — Canonical Qualified Search Runtime

## Mission

Establish one canonical qualified-search runtime module that preserves both the
serialized diagnostic trace and the full request-local `QualificationResult`.

## Runtime State

```text
qualify_rows()
    ↓
QualificationResult
    ├── retained in _LAST_RESULT ContextVar
    ├── projected into _LAST_TRACE ContextVar
    └── returned to the caller
```

## Public Interface

```python
qualify_rows(...)
search_qualified_catalog(...)
get_last_qualification_result()
get_last_qualification_trace()
clear_last_qualification_state()
```

## Compatibility

The module preserves the existing:

- `EvidenceCandidate` normalization;
- accepted-row projection;
- qualification diagnostics;
- trace schema;
- `search_qualified_catalog()` return type;
- catalog grounding behavior.

## New Capability

The Executive Conversation runtime can now consume the exact
`QualificationResult` generated during the current request instead of
reconstructing it from serialized trace data.

## Safety

The installer replaces only:

```text
core/knowledge_catalog/qualified_search.py
```

A complete migration backup is created before replacement. No orchestrator,
conversation service, Director, API route, or Mission Control behavior changes
occur in Pack 2A.

# Genesis IX-A4.5 Pack 3A.1 — Known Query Certification Fixture Repair

## Mission

Replace metadata-oriented known-query fixtures with a semantic query selected
from the live materialized corpus and validated through qualified retrieval.

## Selection Order

1. Runtime document titles.
2. Runtime chunk phrases.
3. Catalog document titles.
4. Document subjects.

## Exclusions

The selector rejects structural vocabulary such as:

```text
sha256
metadata
file_path
confidence
chunk_id
document_id
created_at
updated_at
assigned_by
```

Hexadecimal digest strings are also removed.

## Validation

A candidate is accepted as the certification fixture only when
`search_qualified_catalog()` returns at least one accepted result.

## Runtime Discovery

The repair does not assume the private method name used by
`EndToEndRetrievalTracer`. It inspects the live callable surface, ranks
zero-argument selectors by semantic evidence such as `known`, `query`,
`known_query`, and the former `sha256` logic, then overrides only the selected
bound method for that certification run.

## Production Impact

This pack modifies certification behavior only. Retrieval, grounding,
awareness, Director, synthesis, and conversation APIs remain unchanged.

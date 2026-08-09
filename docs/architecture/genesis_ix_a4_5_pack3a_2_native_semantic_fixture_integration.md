# Genesis IX-A4.5 Pack 3A.2 — Native Semantic Fixture Integration

This pack restores the canonical IX-A4.3 wrapper and repairs known-query
selection inside `EndToEndRetrievalTracer`.

The tracer now builds multi-word semantic candidates from live document titles,
subjects, registry fields, and runtime chunks. Metadata terms and digest-like
hexadecimal strings are excluded. Candidate validation uses
`search_qualified_catalog()`.

The public `certify()` return type remains `EndToEndCertificationReport`.

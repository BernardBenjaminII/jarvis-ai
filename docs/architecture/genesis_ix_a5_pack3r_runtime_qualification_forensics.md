# Genesis IX-A5 Pack 3R — Runtime Qualification Forensics

## Mission

Replace the failed Pack 3 implementation with a self-contained forensic system
that reads the live qualified-search runtime directly.

## Corrections

- Removes the invalid dependency on `dev.knowledge_audit.benchmark`.
- Carries its own canonical probes.
- Uses an injectable provider contract.
- Reads `search_catalog`, `search_qualified_catalog`,
  `get_last_qualification_trace`, and `get_last_qualification_result`.
- Tolerates dictionaries, objects exposing `to_dict()`, sparse traces, and
  missing diagnostics.
- Verifies itself without invoking the broken historical regression chain.

## Safety

Pack 3R is read-only. It does not modify catalog data, FTS indexes,
qualification weights, thresholds, retrieval behavior, grounding, or
orchestration.

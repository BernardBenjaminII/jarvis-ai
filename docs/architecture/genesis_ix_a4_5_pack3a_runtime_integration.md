# Genesis IX-A4.5 Pack 3A — Runtime Integration

Inserts the certified qualification engine between catalog search and
`CatalogGroundingService`.

```text
CatalogGroundingService._search_catalog
        ↓
search_qualified_catalog
        ↓
search_catalog
        ↓
EvidenceCandidate normalization
        ↓
QualificationEngine
        ↓
accepted rows
        ↓
existing GroundingResult construction
```

When every candidate is rejected, the existing `_ground_objective()` receives
an empty result and creates the canonical `KnowledgeGap`.

The installer modifies one exact audited function body and aborts without
changing production code if that body has diverged.

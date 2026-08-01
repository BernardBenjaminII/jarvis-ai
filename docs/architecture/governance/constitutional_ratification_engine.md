# Genesis VII-C3 — Constitutional Ratification Engine

C3 transforms the deterministic C2 relationship graph into a canonical, traceable article-and-section registry.

## Inputs
- `artifacts/audit/km0000-c2/constitutional_analysis.json`
- `artifacts/audit/km0000-c2/constitutional_graph.json`

## Outputs
- `constitutional_ratification.json`
- `constitutional_articles.json`
- `constitutional_sections.json`
- `constitutional_registry.json`
- `constitutional_index.json`
- `constitutional_traceability.json`
- `constitutional_ratification_report.md`

Claims connected by `duplicates`, `supports`, or `refines` form deterministic clusters. Contradictions do not merge clusters and force review unless policy explicitly permits otherwise.

A machine status of `ratified` means the cluster satisfied the declared deterministic policy. Formal constitutional adoption remains a Commander-governed act. C3 does not invent doctrine, use an LLM, rewrite source language, or mutate C0–C2 artifacts.

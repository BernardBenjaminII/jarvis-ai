# Genesis IX-A4.3 — Stage Matrix

| Stage | Certified | Evidence |
|---|---|---|
| Conversation | True | `RUNTIME-CONVERSATION` — The canonical conversation service must be importable. |
| Orchestration | True | `RUNTIME-ORCHESTRATOR` — The conversation service must own an orchestrator. |
| Grounding | True | `RUNTIME-GROUNDING` — The orchestrator must own CatalogGroundingService. |
| Catalog retrieval | True | `KNOWN-EVIDENCE` — A known catalog term must produce evidence. |
| Grounded prompt | True | `KNOWN-GROUNDING-MARKER` — The prompt must contain the canonical grounding section. |
| Knowledge awareness | True | `RUNTIME-AWARENESS` — The orchestrator must own knowledge awareness. |
| Executive Director | True | `RUNTIME-DIRECTOR` — The orchestrator must own ExecutiveDirector. |
| Synthesis | True | `KNOWN-SYNTHESIS` — The orchestrator must invoke synthesis exactly once. |
| Gap handling | True | `GAP-DECLARATION` — Unknown material must generate an explicit KnowledgeGap. |

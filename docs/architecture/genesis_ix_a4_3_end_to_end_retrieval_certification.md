# Genesis IX-A4.3 — End-to-End Retrieval Certification

## Mission

Certify the complete Mark I retrieval path from an operator question through
grounding, retrieval, knowledge awareness, Executive direction, and synthesis.

## Method

Certification performs two real conversation requests:

1. A known query automatically derived from the live catalog.
2. A deliberately unknown query that must produce a KnowledgeGap.

The live conversation service and catalog are used. The synthesis handler is
temporarily replaced inside the certification process with a deterministic
capture function. This prevents external model invocation while preserving the
real Executive, grounding, retrieval, awareness, and response pipeline.

The original synthesis handler is restored in a `finally` block.

## Certified Path

```text
Operator question
    ↓
ExecutiveConversationService
    ↓
ExecutiveConversationOrchestrator
    ↓
CatalogGroundingService
    ↓
search_catalog
    ↓
search_runtime_knowledge
    ↓
runtime_chunks_fts
    ↓
GroundingResult or KnowledgeGap
    ↓
ExecutiveKnowledgeAwarenessService
    ↓
ExecutiveDirector
    ↓
grounded synthesis prompt
```

## Outputs

```text
docs/audits/genesis_ix_a4_3/
    end_to_end_certification.json
    end_to_end_certification.md
    known_retrieval_trace.md
    gap_retrieval_trace.md
    stage_matrix.md
    grounded_prompt_contract.md
```

## Safety

IX-A4.3 introduces no production retrieval behavior and invokes no external
model during certification.

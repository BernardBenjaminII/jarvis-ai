# Genesis X-B1.1a — Embedding Reliability & Failure Isolation

Preserves existing semantic state and hardens batch execution.

- RETRY before PENDING
- bounded retry/backoff
- HTTP body/status capture
- recursive split 8→4→2→1
- only individually persistent failures become REJECTED
- vector count/dimension/finiteness validation
- expected mxbai-embed-large dimension: 1024
- append-only embedding_failures diagnostics

The canonical runtime corpus remains read-only.

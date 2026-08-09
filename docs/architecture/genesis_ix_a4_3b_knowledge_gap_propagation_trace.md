# Genesis IX-A4.3B — Knowledge Gap Propagation Trace

Traces a KnowledgeGap through:

```text
grounding.result
awareness.input
awareness.output
director.input
director.output
synthesis.prompt
conversation.response
```

The tracer temporarily wraps live bound methods and restores them in a `finally` block. The synthesis handler is replaced only during tracing with a deterministic prompt capture, so no external model is invoked.

Possible verdicts:

```text
RUNTIME_DEFECT
CERTIFICATION_DEFECT
DATA_DEFECT
CONFIGURATION_DEFECT
```

Outputs are written under `docs/audits/genesis_ix_a4_3b/`.

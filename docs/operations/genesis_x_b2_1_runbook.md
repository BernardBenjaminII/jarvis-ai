# Genesis X-B2.1 Runbook

Start with audit:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b2_1 audit
```

Run a bounded semantic canary:

```bash
time "$PYTHON_BIN" -m dev.run_genesis_x_b2_1 query \
  --query "How do C++ iterators work?" \
  --top-k 10 \
  --scan-limit 25000
```

Then run a larger retrieval canary:

```bash
time "$PYTHON_BIN" -m dev.run_genesis_x_b2_1 query \
  --query "What are the principles of evidence-based reasoning?" \
  --top-k 10 \
  --scan-limit 250000
```

Finally certify:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_b2_1 certify
```

Do not begin full-index latency optimization until candidate correctness,
provenance, vector dimensions, and read-only safety certify cleanly.

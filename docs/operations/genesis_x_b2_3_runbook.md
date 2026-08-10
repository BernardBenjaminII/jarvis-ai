# Genesis X-B2.3 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b2_3 audit

time "$PYTHON_BIN" -m dev.run_genesis_x_b2_3 assemble \
  --query "How do C++ iterators work?" \
  --top-k 8 \
  --candidate-pool 60 \
  --scan-limit 25000 \
  --neighbor-radius 1 \
  --max-chars 12000

"$PYTHON_BIN" -m dev.run_genesis_x_b2_3 certify
```

Expected qualitative behavior:

- zero-signal Python/C/Arduino passages should be filtered,
- strong C++ iterator/STL anchors should remain,
- nearby explanatory chunks may appear as neighbor evidence,
- redundant copies should not consume the context budget,
- total selected context must remain within the requested character budget.

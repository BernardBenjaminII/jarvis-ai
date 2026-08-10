# Genesis X-B2.2 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b2_2 audit

time "$PYTHON_BIN" -m dev.run_genesis_x_b2_2 query \
  --query "How do C++ iterators work?" \
  --top-k 10 \
  --candidate-pool 50 \
  --scan-limit 25000

"$PYTHON_BIN" -m dev.run_genesis_x_b2_2 certify
```

Expected qualitative result:

- true C++ iterator/STL evidence should rise above generic for-loop iteration,
- duplicate passages should collapse,
- the final top-K should contain more diverse evidence than X-B2.1.

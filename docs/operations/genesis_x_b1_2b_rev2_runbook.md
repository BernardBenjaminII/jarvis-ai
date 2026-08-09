# Genesis X-B1.2b Revision 2 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2b_rev2 audit

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2b_rev2 reconcile

time "$PYTHON_BIN" -m dev.run_genesis_x_b1_2b_rev2 recover   --batch-size 8

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2b_rev2 status
"$PYTHON_BIN" -m dev.run_genesis_x_b1_2b_rev2 certify
```

Do not resume the 5,000-parent corpus campaign until this repair certifies cleanly.

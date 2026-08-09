# Genesis X-A1.1 Runbook

## Recover the interrupted queue

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.repair_genesis_x_a1_1_state
```

## Verify queue state

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a1 status
```

Expected:

```text
CHUNKED: 0
EXTRACTING: 0
WRITING: 0
FAILED lock candidate recovered
VALIDATED increased
```

## Verify SQLite policy

```bash
sqlite3 /media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite "
PRAGMA journal_mode;
PRAGMA busy_timeout;
"
```

Expected:

```text
wal
30000
```

## Repeat the 100-document canary

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a1   execute   --workers 4   --batch-size 100   --stop-on-error
```

## Review

```bash
cat docs/audits/genesis_x_a1/execution_report.md

"$PYTHON_BIN" -m dev.run_genesis_x_a1 status
```

# Genesis IX-A6 Campaign Runbook

## 1. Prepare the candidate registry

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_ix_a6_materialization prepare
```

## 2. Inspect campaign status

```bash
"$PYTHON_BIN" -m dev.run_genesis_ix_a6_materialization status
```

## 3. Run a 25-document dry run

```bash
"$PYTHON_BIN" -m dev.run_genesis_ix_a6_materialization   dry-run   --batch-size 25   --max-batches 1
```

## 4. Run the first production canary

```bash
"$PYTHON_BIN" -m dev.run_genesis_ix_a6_materialization   execute   --batch-size 10   --max-batches 1   --stop-on-error
```

## 5. Review the production report

```bash
cat docs/audits/genesis_ix_a6/execution_report.md
```

Verify:

- runtime documents increased;
- runtime chunks increased;
- FTS rows increased by the same number as runtime chunks;
- no candidate was quarantined;
- no extraction failure occurred.

## 6. Scale progressively

Recommended sequence:

```text
10 documents
25 documents
100 documents
500 documents
1,000 documents per invocation
```

Do not immediately launch the entire corpus in one process.

## 7. Resume

Repeat the execute command. The checkpoint store automatically selects the next
pending candidates.

## 8. Retry failures

Only after reviewing failure details:

```bash
"$PYTHON_BIN" -m dev.run_genesis_ix_a6_materialization   execute   --batch-size 25   --max-batches 1   --retry-failures   --stop-on-error
```

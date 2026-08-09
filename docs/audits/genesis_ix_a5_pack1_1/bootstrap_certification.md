# Genesis IX-A5 Pack 1.1 — Bootstrap Certification

**Status:** **FAILED**
**Checks passed:** 5/6

| Check | Status | Detail |
|---|---|---|
| `ROOT-VALID` | **PASS** | /media/abdullah/JARVISDATA/Projects/jarvis-ai |
| `CONTEXT-IMMUTABLE` | **PASS** | RuntimeContext is frozen |
| `JSON-SERIALIZATION` | **PASS** | RuntimeContext serializes |
| `SYSPATH-UNIQUE` | **PASS** | count=1 |
| `ARBITRARY-CWD` | **FAIL** | Traceback (most recent call last):
  File "/media/abdullah/JARVISDATA/Projects/jarvis-ai/dev/run_genesis_ix_a5_pack1_audit.py", line 164, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/media/abdullah/JARVISDATA/Projects/jarvis-ai/dev/run_genesis_ix_a5_pack1_audit.py", line 151, in main
    print("Database       :", data["database"]["path"])
                              ~~~~^^^^^^^^^^^^
KeyError: 'database' |
| `AUDIT-REPORT` | **PASS** | report generated outside repository cwd |

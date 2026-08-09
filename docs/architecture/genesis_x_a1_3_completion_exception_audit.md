# Genesis X-A1.3 — Materialization Completion & Exception Audit

Read-only completion certification for X-A1. It reconciles the checkpoint with the runtime database, validates SQLite integrity and chunk/FTS parity, classifies every FAILED candidate, inspects source file state, and produces retry/quarantine recommendations. It assumes 69 runtime documents pre-existed the campaign; this is configurable.

# Genesis X-A1.2 — High-Throughput Materialization Pipeline

X-A1.2 adds bounded scheduling, explicit backpressure, a single dedicated SQLite
writer, grouped writer transactions, live telemetry, and safe reuse of the X-A1
checkpoint database.

Defaults: 6 workers, 24 in-flight jobs, artifact queue 32, writer batch 20.

The scheduler never submits the entire corpus at once. Extraction cannot run
arbitrarily far ahead of SQLite. `runtime_chunks == runtime_chunks_fts` remains
a required integrity invariant.

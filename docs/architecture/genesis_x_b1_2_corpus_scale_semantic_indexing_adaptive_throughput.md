# Genesis X-B1.2 — Corpus-Scale Semantic Indexing & Adaptive Throughput

## Mission

Productionize the semantic campaign across the full runtime corpus while
preserving all X-B1.1/X-B1.1a/X-B1.1b guarantees.

## Principles

- canonical runtime corpus remains read-only
- existing semantic vectors are reused
- RETRY is processed before PENDING
- provider failures use bounded retry and isolation
- context overflows route into recursive semantic fragmentation
- system load and available memory trigger backpressure
- campaign state is resumable
- progress, throughput, remaining work, and ETA are surfaced

## Production Campaign

Recommended escalation:

1. 1,000-item canary
2. 5,000-item batch
3. 25,000-item batch
4. sustained large campaign

Do not start the full corpus in one invocation until sustained throughput and
thermal stability are established.

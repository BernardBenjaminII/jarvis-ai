# Genesis X-B1.2b — Predictive Context Routing & Throughput Optimization

Predictive preflight routes chunks directly to semantic fragmentation when:

- character length >= 2250, or
- existing token estimate >= 560.

These thresholds are based on the production rejection boundary observed in X-B1.2a.

The pack retains recursive fallback for any mispredicted context overflow, corrects
`fragmented_complete` to use authoritative before/after parent deltas, measures
successful-parent throughput, and reports vector amplification.

# ADR-0026 — Executive Observation Bus

**Status:** Accepted

JARVIS shall use `core.cognition.observation` as the canonical observation
publication namespace. Observations must be immutable, timezone-aware,
provenance-bearing, confidence-scored, JSON-compatible, deterministic, and
idempotently publishable.

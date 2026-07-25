# ADR-0027 — Executive Situation Model

**Status:** Accepted  
**Date:** 2026-07-24  
**Decision owner:** Genesis IV-A2

## Context

IV-A1 provides trustworthy observations, but executive cognition cannot reason
effectively over an unstructured flat stream.

Observations must be grouped into auditable situations before hypothesis
generation begins.

## Decision

JARVIS shall establish `core.cognition.situation` as the canonical owner of
executive situation representations.

A situation shall:

- contain at least one IV-A1 observation;
- preserve every source observation;
- permit explicit observation relations;
- derive confidence and severity deterministically;
- preserve mission and correlation context when consistent;
- receive a deterministic semantic identifier;
- remain immutable after construction.

## Consequences

The cognitive pipeline gains a stable boundary between observation and
hypothesis.

The model supports transparent graph visualization while refusing to invent
relations that were not supplied or proven.

Persistent repositories and incremental mutation remain deferred.

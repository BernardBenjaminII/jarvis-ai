# ADR-EXEC-0004: Read-Only Knowledge Inventory Projection

**Status:** Accepted  
**Date:** 2026-07-23

## Context

JARVIS contains multiple mature knowledge stores, but Mission Control cannot
observe their runtime state through the Executive Projection Plane.

A complete semantic knowledge projection is too large for a single safe
integration phase.

## Decision

UI-A4 will be delivered incrementally. UI-A4.1 establishes a read-only
inventory provider that observes the configured knowledge root and SQLite
stores.

The provider will use bounded filesystem scanning, read-only SQLite
connections, caching, and explicit degradation states.

## Consequences

- Mission Control gains truthful knowledge-estate visibility.
- Existing knowledge schemas remain authoritative.
- No new catalog database is introduced.
- Large scans are bounded and cached.
- Semantic interpretation is deferred to UI-A4.2 and later installments.

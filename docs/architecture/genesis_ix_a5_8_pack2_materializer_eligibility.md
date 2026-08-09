# Genesis IX-A5.8 Pack 2 — Materializer Eligibility and Candidate Selection Audit

## Mission

Determine why classified knowledge records do or do not become runtime
documents.

## Read-Only Guarantee

The pack does not modify catalogs, files, lifecycle states, runtime documents,
chunks, or FTS indexes.

## Deterministic Dispositions

- `ALREADY_MATERIALIZED`
- `ELIGIBLE_NOT_SELECTED`
- `UNSUPPORTED_MEDIA_TYPE`
- `CONTAINER_OR_ARCHIVE`
- `MISSING_SOURCE_FILE`
- `UNREADABLE_SOURCE`
- `EMPTY_SOURCE`
- `DUPLICATE_SOURCE`
- `DEFERRED_BY_POLICY`
- `FAILED_EXTRACTION`
- `FAILED_MATERIALIZATION`
- `UNKNOWN`

## Authority Model

Inventory metadata and runtime retrieval are treated as separate authorities.
The audit uses the runtime classification table as the candidate population when
available and resolves physical paths against the knowledge root.

## Decision Boundary

A large `ELIGIBLE_NOT_SELECTED` population proves that candidate selection or
campaign scope—not FTS ranking—is the next repair target.

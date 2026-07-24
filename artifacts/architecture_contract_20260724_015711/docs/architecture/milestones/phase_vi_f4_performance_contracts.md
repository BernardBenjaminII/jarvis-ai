# JARVIS Gen 2 — Phase VI-F4

# Determinism and Performance Contracts

**Status:** Complete after focused and master verification pass.

---

## Purpose

Phase VI-F4 establishes reproducibility and bounded-performance contracts for
the controlled assimilation core.

The phase does not attempt to define competitive benchmark scores. Hardware,
filesystems, Python builds, and operating systems vary.

Instead, VI-F4 protects the system from severe regressions by verifying that
core operations remain deterministic, stateless, bounded, and internally
consistent.

---

## Scope

The phase measures and verifies:

- document extraction determinism
- checksum determinism
- chunk determinism
- source-collection planning determinism
- repository-read determinism
- repository lookup bounds
- Runner construction cost
- Runner construction memory
- independent default service composition
- temporary-catalog end-to-end assimilation

The live JARVIS catalog is never opened.

---

## Determinism contracts

Given identical input and configuration, repeated extraction must produce:

- identical normalized text
- identical checksum
- identical chunk count
- identical chunk ordering
- identical chunk boundaries
- identical extractor metadata

Repeated collection planning must produce an identical serialized plan.

Repeated repository reads must produce equal immutable objects.

---

## Service-state contract

ExtractionService must not accumulate hidden mutable state between calls.

The service configuration before and after repeated extraction must remain
identical.

---

## Runner construction contract

Constructing AssimilationRunner must remain lightweight.

Construction must not:

- open a transaction
- perform extraction
- write persistence records
- journal attempts
- mutate lifecycle state
- scan the filesystem
- perform network access

Each Runner must receive independent default service instances.

---

## Performance philosophy

VI-F4 uses generous safety ceilings rather than hardware-specific targets.

The test fails only when behavior indicates a material regression, such as:

- extraction becoming unreasonably slow
- repository reads becoming unbounded
- Runner construction allocating excessive memory
- end-to-end processing becoming unexpectedly expensive
- deterministic output changing across identical runs

Recorded metrics are diagnostic and may vary between machines.

---

## Temporary fixtures

Every test uses:

- temporary directories
- temporary source documents
- temporary SQLite catalogs
- deterministic local content

The production knowledge catalog and external network are not used.

---

## Metrics reported

The verification suite reports:

- extraction source size
- extraction elapsed time
- extraction throughput
- extraction chunk count
- collection-plan serialized size
- repository lookups per second
- Runner constructions per second
- Runner construction peak memory
- end-to-end documents per second
- total chunks
- average chunks per document

These metrics establish an operational reference for future comparisons.

---

## Verification

Focused verification:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_phase_6f4.sh

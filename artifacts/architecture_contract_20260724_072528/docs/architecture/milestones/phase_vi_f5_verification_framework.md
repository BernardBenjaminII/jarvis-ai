# JARVIS Gen 2 — Phase VI-F5

# Verification Framework Consolidation

**Status:** Complete after focused and master verification pass.

---

## Purpose

Phase VI-F5 replaces the hand-maintained master shell loop with a canonical,
tested verification framework.

Existing phase verification scripts remain independent and executable. The
framework provides one registry, one execution model, one summary format, and
one machine-readable report format.

---

## Architecture

```text
verify_all.sh
      │
      ▼
dev.verification.runner
      │
      ├── registry
      ├── suite execution
      ├── timing
      ├── output capture
      ├── required/optional policy
      ├── console reporting
      └── JSON reporting
              │
              ▼
      verify_phase_*.sh

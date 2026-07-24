# JARVIS Gen 2 — Phase VI-F7

# Developer Infrastructure and Safe Commit Gate

**Status:** Complete after focused verification, master verification, safe
commit rehearsal, and successful milestone push.

---

## Purpose

Phase VI-F7 protects the development process surrounding JARVIS.

The phase introduces a safe-commit gate, continuous verification workflow,
machine-readable CI reports, and permanent developer-release rules.

No assimilation runtime behavior is changed.

---

## Safe-commit workflow

```text
Reviewed staged files
        ↓
Repository health
        ↓
Index and merge-state validation
        ↓
Whitespace and conflict checks
        ↓
Focused verification
        ↓
Master verification
        ↓
JSON verification report
        ↓
Commit
        ↓
Optional push

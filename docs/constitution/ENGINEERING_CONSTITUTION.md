# JARVIS Engineering Constitution

**Status:** Foundational  
**Authority:** Commander-approved engineering doctrine  
**Scope:** All code, tooling, documentation, migrations, certifications, and releases

## Preamble

The Engineering Operating System ensures that implementation does not outrun
understanding, automation does not outrun authority, and growth does not create
hidden architectural uncertainty.

## Principles

1. **Explicit Ownership:** Every concept and public contract has one canonical owner.
2. **Contract Before Implementation:** Stable boundaries are explicit before runtime dependence.
3. **Deterministic Evidence:** Equivalent state produces equivalent analysis and fingerprints.
4. **Verification Is Architecture:** A capability is incomplete until behavior, boundaries, and regressions are verified.
5. **Compatibility Is Explicit:** Certified APIs remain compatible unless an approved breaking change exists.
6. **Explainability Must Increase:** Every architectural change leaves the repository more explainable than before.
7. **Human Authority:** Deletion, breaking migration, and release approval require explicit human authority.
8. **Deletion Requires Evidence:** Ownership, dependencies, compatibility, migration, and regressions must support removal.
9. **Least Authority:** Read-only intelligence remains separate from source-changing automation.

## Change Classes

- Feature Pack
- Certification Pack
- Evolution Pack
- Repair Pack
- Migration Pack
- Retirement Pack

## Development Lifecycle

```text
Need
  ↓
Architecture
  ↓
Ownership
  ↓
Contracts
  ↓
Implementation
  ↓
Verification
  ↓
Certification
  ↓
Evolution Plan
  ↓
Commit
  ↓
Release
```

## Required Questions

Every material change must answer:

1. Who owns the concept?
2. Which contracts define it?
3. Which public APIs may change?
4. How is compatibility preserved or migrated?
5. How is the change verified?
6. What is the rollback strategy?
7. What uncertainty remains?
8. How does explainability improve?

## Governing Maxim

> Every architectural change must leave the repository more explainable than before it began.

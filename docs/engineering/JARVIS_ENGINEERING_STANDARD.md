# JARVIS Engineering Standard

## Philosophy

Every subsystem should be:

- Modular
- Testable
- Replaceable
- Documented
- Independently verifiable

---

## Layering

CLI

↓

Workflow

↓

Capability

↓

Service

↓

Implementation

↓

Storage

---

## Every subsystem must contain

- Implementation
- Service
- Capability
- CLI
- Workflow integration
- Verification
- Doctor support
- Documentation

---

## Verification

Every milestone must end with:

Compile

↓

Verification

↓

Workflow Test

↓

Doctor

↓

Git Commit

---

## Never

Never rewrite working code when a wrapper or service layer can preserve proven functionality.

---

## Git

Prefer small subsystem commits over large feature commits.

Every commit should represent a stable, working checkpoint.

---

## Documentation

Every architectural decision receives an ADR.

Every subsystem receives documentation.

Every verification tool documents expected output.

---

## Definition of Done

A subsystem is complete only when:

- Code compiles.
- Verification passes.
- Workflow passes.
- Doctor reports healthy.
- Documentation is updated.
- Git history contains a clean checkpoint.

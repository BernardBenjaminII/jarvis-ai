# JARVIS Gen 2 — Phase VII-A2

# Deterministic Acquisition Admission Engine

## Status

Complete after focused verification, master verification, commit, and push.

## Purpose

Phase VII-A2 introduces a deterministic decision layer between acquisition
discovery and durable acquisition processing.

Every discovered `SourceCandidate` is evaluated by an ordered admission-policy
registry and receives one canonical action:

- `accept`
- `review`
- `ignore`
- `reject`

The admission subsystem is read-only. It does not persist records, mutate
source files, enqueue work, or invoke assimilation.

## Architecture

```text
SourceCandidate
        │
        ▼
AdmissionDirector
        │
        ▼
AdmissionPolicyRegistry
        │
        ├── ExactDuplicatePolicy
        ├── ExtensionAdmissionPolicy
        ├── SizeAdmissionPolicy
        └── ClassificationAdmissionPolicy
        │
        ▼
AdmissionDecision

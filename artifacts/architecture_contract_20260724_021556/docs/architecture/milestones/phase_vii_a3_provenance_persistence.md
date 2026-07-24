# JARVIS Gen 2 — Phase VII-A3

# Provenance Persistence Foundation

## Purpose

Phase VII-A3 gives the acquisition subsystem durable memory of every source
encountered and every admission decision made.

## Persistent records

The provenance layer records:

- deterministic candidate identity
- provider ID
- source URI
- local path and filename
- current SHA-256 checksum
- first-seen timestamp
- last-seen timestamp
- sighting count
- latest admission action
- latest decision fingerprint
- campaign identity
- complete admission-decision history

## Architecture

```text
AdmissionDecision
        ↓
ProvenanceService
        ↓
ProvenanceRepository
        ↓
SQLite
        ├── acquisition_provenance
        └── acquisition_admission_history

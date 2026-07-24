# JARVIS Gen 2 — Phase VII-A4

# Durable Admission Workflow

## Purpose

Phase VII-A4 connects acquisition admission to persistent provenance.

JARVIS no longer requires callers to manually provide known checksums.
The intake service automatically loads durable checksum memory, evaluates the
candidate, and records the resulting admission decision and sighting.

## Architecture

```text
SourceCandidate
      ↓
AcquisitionIntakeService
      ├── ProvenanceService.known_checksums()
      ├── AdmissionDirector.evaluate_candidate()
      └── ProvenanceService.record_decision()
      ↓
AcquisitionIntakeResult

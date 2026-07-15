# JARVIS Gen 2 — Phase VII-A5

# Durable Acquisition Missions

## Purpose

Phase VII-A5 converts provenance-backed intake results into durable acquisition
missions.

Every candidate result is preserved as:

- accepted
- review
- ignored
- rejected

## Architecture

```text
AcquisitionIntakeResult
        ↓
AcquisitionMissionService
        ↓
acquisition_missions
        ↓
acquisition_mission_items

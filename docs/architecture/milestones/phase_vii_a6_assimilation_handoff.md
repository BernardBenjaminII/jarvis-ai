# JARVIS Gen 2 — Phase VII-A6

# Controlled Assimilation Handoff

## Purpose

Phase VII-A6 establishes the protected boundary between durable acquisition
missions and the Phase VI assimilation subsystem.

Only mission items classified as `accepted` may produce assimilation handoff
requests.

## Architecture

```text
AcquisitionMission
        ↓
accepted items only
        ↓
AssimilationHandoffService
        ↓
acquisition_assimilation_handoffs
        ↓
future canonical assimilation dispatcher

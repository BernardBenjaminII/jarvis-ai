# Genesis VII-A0 — Pack 3B-2.2

## Executive Health and Runtime Projection

**Status:** Implemented

**Depends on:**

- Genesis VII-A0 Pack 2
- Genesis VII-A0 Pack 3A-3.1
- Genesis VII-A0 Pack 3B-1
- Genesis VII-A0 Pack 3B-2.1

## Purpose

Pack 3B-2.2 projects canonical Executive dashboard telemetry into the
Commander Brief Operational Picture.

## Projected Capabilities

- Executive Health state
- Health-check inventory
- Executive attention items
- Python runtime version
- Logical CPU count
- system load averages
- memory availability
- project-filesystem utilization
- root-filesystem utilization
- available metric-card values
- workstream summaries
- metric-source availability summary

## Canonical Data Source

GET /operations/executive/dashboard

Constitutional Rules
The projection shall consume only authoritative API data.
Missing values shall remain visibly unavailable.
Registry metrics shall not be fabricated.
Storage warning states shall derive from measured utilization.
Attention items shall derive from Executive Status.
The projection shall not modify the Executive runtime.
The projection shall not establish WebSocket behavior.
API requests may use an extended initial timeout because filesystem
inventories can exceed ten seconds.

# Genesis VII-A0 — Pack 3B-2.1

## Executive Status Banner Projection

**Status:** Implemented

**Depends on:**

- Genesis VII-A0 Pack 2
- Genesis VII-A0 Pack 3A-3.1
- Genesis VII-A0 Pack 3B-1

## Purpose

Pack 3B-2.1 establishes the first live Commander Brief projection.

It retrieves the canonical Executive Dashboard response and projects its
status model into the Executive Status Banner.

## Projected Fields

- overall Executive state;
- Executive status headline;
- primary attention message;
- Executive health state;
- available metric summary;
- generated timestamp;
- status-bar health;
- status-bar update time.

## Data Source

```text
GET /operations/executive/dashboard

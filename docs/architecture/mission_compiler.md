# JARVIS Mission Compiler Architecture

## Status

Phase IX-C2A — Deterministic Foundation

## Purpose

The Mission Compiler is the controlled transformation boundary between
immutable mission planning and mutable runtime execution.

It prevents the Executive runtime from interpreting planning structures
directly and prevents planning contracts from acquiring execution behavior.

## Model distinction

JARVIS intentionally maintains two mission representations.

### Planning Mission

Canonical location:

```text
core.executive.planning.models.Mission

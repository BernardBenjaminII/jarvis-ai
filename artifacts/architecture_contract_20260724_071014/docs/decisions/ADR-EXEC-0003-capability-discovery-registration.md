# ADR-EXEC-0003: Capability Discovery and Registration

**Status:** Accepted  
**Date:** 2026-07-23

## Context

The capability framework already provided registration, dependency resolution,
loading, and execution. The Executive Projection Plane initially created an
empty process-local registry because no real subsystem capabilities were bound
to it.

## Decision

JARVIS will populate the canonical registry through two mechanisms:

1. mandatory built-in capability registration for process-local foundational
   services
2. recursive package discovery through explicit `register_capabilities` hooks

Capabilities must expose truthful binding metadata. The system will not infer
that an implementation is executable merely because it has been discovered.

## Consequences

- Mission Control can show what JARVIS can actually do.
- Discovery failures become observable.
- Capability dependencies remain canonical.
- Subsystems own their registration hooks.
- Transport code remains independent of subsystem implementations.
- Remote execution remains prohibited until a governed execution phase.

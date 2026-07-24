# JARVIS Convergence C-2 — Director Activation

## Purpose

C-2 puts the existing Executive Director, Mission Planner, Director Registry,
Mission Engine, and Mission Store to work behind the C-1 conversation boundary.
It does not create a second director hierarchy or replace established contracts.

## Canonical request path

```text
Operator request
  -> ExecutiveConversationService
  -> ExecutiveRequestCompiler
  -> ExecutiveConversationOrchestrator
  -> ExecutiveDirector.submit
  -> MissionPlanner
  -> DirectorRegistry
  -> MissionEngine
  -> Director handlers
  -> Executive synthesis adapter
  -> conversation response
```

Each compiled objective becomes one persisted executive mission. The response
metadata exposes mission IDs, directors activated, task lifecycle, capability
requirements, routing evidence, results, and errors. The existing answer path is
retained only as the synthesis adapter until C-3 and C-4 progressively connect
capability routing and grounded knowledge/reasoning.

## Architectural rules

1. The UI calls only the canonical conversation API.
2. Conversation code delegates through `ExecutiveDirector`; it does not call
   subordinate director handlers directly.
3. Existing mission persistence and execution semantics remain authoritative.
4. Director activity is transparent in the response metadata and trace.
5. C-1 API, persistence, and UI contracts remain backward compatible.

## Completion contract

C-2 is complete when a text or voice-channel request creates mission work for
each compiled objective, activates the applicable registered directors, executes
the mission, persists the work, returns one response, and exposes the director
activity without breaking C-1.

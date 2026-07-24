# Genesis VI-A2 — Executive Working Memory

**Status:** Implemented  
**Package:** `core.cognition`  
**Primary module:** `core/cognition/working_memory.py`

## Purpose

Genesis VI-A2 introduces the bounded executive scratchpad used by later
cognition cycles. The component stores temporary mission-relevant information
without becoming a durable knowledge repository.

## Capabilities

- configurable bounded capacity;
- admission by immutable entry identifier;
- deterministic retention ordering;
- duplicate rejection;
- priority-based deterministic eviction;
- rejection of entries that do not outrank retained information;
- lookup by identifier;
- lookup by memory-entry kind;
- complete replacement;
- controlled field updates;
- removal and discard operations;
- immutable detached snapshots;
- deterministic bulk admission.

## Retention Policy

Entries are ranked using the following retention key:

1. importance;
2. confidence;
3. creation timestamp;
4. entry identifier.

Higher values are retained. The identifier is the final stable tie-breaker.

When memory is full, the weakest retained entry is compared with the incoming
entry. Eviction occurs only when the incoming entry is strictly stronger.
Otherwise admission fails without modifying memory.

## Architectural Boundaries

Working memory:

- does not call a language model;
- does not retrieve external knowledge;
- does not plan;
- does not execute;
- does not persist itself;
- does not mutate `MemoryEntry` objects.

Durable episodic memory, semantic memory, and archival persistence are outside
this phase.

## Public API

- `WorkingMemory`
- `WorkingMemorySnapshot`

The existing Genesis VI-A1 public contracts remain stable.

## Next Phase

Genesis VI-A3 will introduce the deterministic cognitive state machine and
validated lifecycle transitions.

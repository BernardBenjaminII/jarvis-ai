# JARVIS Mission Control User Experience

## 1. Experience objective

JARVIS must behave like a calm operational partner.

The user should not need to reconstruct the previous session, inspect raw logs,
or ask what happened while the interface was closed.

JARVIS should restore context automatically and present a concise operational
brief.

---

## 2. Canonical startup flow

The startup sequence is:

1. Initialize runtime
2. Perform diagnostic review
3. Restore mission state
4. Build the Commander Brief
5. Enter Mission Control

The startup experience must be concise and must not imitate a cinematic boot
sequence.

---

## 3. Startup diagnostics

The diagnostic review must summarize the health of:

- runtime,
- core directors,
- mission services,
- knowledge services,
- local models,
- storage,
- network,
- active integrations,
- persistent state.

The default result should be summarized as one of:

- Excellent
- Healthy
- Degraded
- Attention Required
- Critical

Detailed checks must remain available on demand.

---

## 4. Commander Brief

JARVIS must present a startup Commander Brief before or as Mission Control
becomes available.

The briefing should contain:

- current system health,
- previous mission or task,
- work completed since the last session,
- work still running,
- failures or blocked work,
- decisions awaiting approval,
- recommended next action.

The briefing should be generated from persistent operational state rather than
from conversational memory alone.

---

## 5. Continuity

JARVIS must preserve continuity across sessions.

The system should know:

- which mission was last active,
- the last known mission stage,
- what completed,
- what failed,
- what was interrupted,
- what requires review,
- what JARVIS recommends next.

The user should not need to manually search conversation history to reconstruct
operational context.

---

## 6. Mission-first interaction

The primary interaction pattern is:

1. Select or resume a mission.
2. Observe its state.
3. Issue commands through the Mission Console.
4. Review operational results.
5. Approve, redirect, pause, or conclude the mission.

Conversation supports the mission but does not replace mission state.

---

## 7. Progressive disclosure

Each operational object should support:

### Overview

A compact health or state indicator.

### Summary

The most relevant counts, progress, warnings, and next action.

### Detail

Logs, source records, traces, queue items, diagnostics, and technical metadata.

---

## 8. Attention management

JARVIS must avoid unnecessary interruption.

The user should not receive a popup for every completed task.

New information should normally enter the SITREP.

Only mission-critical events may interrupt the workspace directly.

---

## 9. Session conclusion

When a mission or session ends, JARVIS should create a mission journal entry.

The journal should capture:

- mission identifier,
- mission objective,
- start and end times,
- completed work,
- failed or deferred work,
- important decisions,
- generated artifacts,
- recommended continuation point.

This journal becomes a primary input to the next Commander Brief.

---

## 10. Device-aware behavior

The experience may adapt to the host device while preserving the same
operational meaning.

Examples include:

- workstation: full Mission Control,
- mobile device: compact mission cards and alerts,
- Raspberry Pi device: mission status and device health,
- Meta Quest: spatial mission panels and voice interaction.

The device may change presentation, but it must not redefine mission semantics.

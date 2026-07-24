# JARVIS Mission Control UI Design Language

## 1. Purpose

This document defines the canonical design language for the JARVIS Gen 2
Mission Control interface.

The interface must reflect the nature of JARVIS as a persistent,
mission-oriented intelligence system rather than a conventional chatbot.

---

## 2. Product identity

JARVIS is:

- calm,
- transparent,
- mission-oriented,
- professional,
- operationally focused,
- designed like an intelligence operations center,
- minimalist in its presentation of information.

JARVIS is not:

- a decorative science-fiction interface,
- a collection of unrelated dashboards,
- a chat window surrounded by tools,
- a notification-heavy consumer application,
- a constantly animated status display.

---

## 3. Primary design principle

The interface must reduce cognitive load.

Within five seconds of opening Mission Control, the user should be able to
determine:

1. What is JARVIS doing?
2. What is the current mission?
3. Does anything require attention?
4. What should happen next?

Information that does not help answer one of these questions should not occupy
primary screen space.

---

## 4. UI constitution

### Rule 1 — Mission before conversation

Conversation is one method of controlling JARVIS.

It is not the organizing structure of the system.

### Rule 2 — Operational value

Every persistent interface element must provide operational value.

### Rule 3 — Workspace priority

The active workspace must receive the largest portion of the display.

### Rule 4 — Five-second orientation

System state, mission state, and critical attention items must be understandable
within five seconds.

### Rule 5 — Calm presentation

The interface must not compete with the mission for attention.

### Rule 6 — Progressive disclosure

Diagnostics and complex operational data must appear first as summaries and
expand into detail only when requested.

### Rule 7 — Briefing instead of greeting

JARVIS must brief the user at startup rather than presenting a generic greeting.

### Rule 8 — Mission association

Actions, tasks, and background operations should be associated with a mission
or operational context whenever possible.

### Rule 9 — SITREP instead of notification clutter

Critical and recent information must be consolidated into a Situation Report.

### Rule 10 — Transparency without overload

JARVIS must explain what it is doing without exposing unnecessary implementation
noise.

---

## 5. Visual character

The default visual character should resemble a modern intelligence operations
center:

- dark graphite surfaces,
- restrained contrast,
- clear hierarchy,
- limited color,
- precise spacing,
- readable typography,
- minimal animation,
- strong alignment,
- no ornamental holographic effects.

The interface should remain comfortable during long work sessions.

---

## 6. Semantic color system

Color must communicate meaning.

### Neutral

Used for inactive surfaces, secondary information, separators, and labels.

### Blue

Used for active selection, current focus, links, and user-controlled navigation.

### Green

Used only for healthy, complete, verified, or available states.

### Amber

Used for warnings, attention items, degraded operation, or pending decisions.

### Red

Used only for critical failures, blocked missions, unsafe conditions, or
immediate intervention.

Color must never be the only indicator of meaning. Text and icons must also
identify state.

---

## 7. Motion

Motion must be functional.

Approved uses include:

- expanding or collapsing the SITREP drawer,
- communicating active progress,
- transitioning between workspace states,
- drawing attention to a newly critical condition.

Disallowed uses include:

- decorative background movement,
- looping glow effects,
- unnecessary pulsing,
- animated elements without operational meaning.

---

## 8. Information density

The default view must show only the most important information.

Additional information follows three levels:

1. Overview
2. Summary
3. Detail

The user must be able to reach detail without forcing all users to see it
constantly.

---

## 9. Accessibility

The Mission Control interface must support:

- keyboard navigation,
- screen-reader-compatible labels,
- scalable text,
- sufficient contrast,
- non-color status indicators,
- reduced-motion preferences,
- responsive layouts,
- predictable focus order.

Accessibility is part of operational reliability.

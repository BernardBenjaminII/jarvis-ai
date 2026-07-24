# ADR-0018 — Operational Memory as a First-Class Architectural Domain

**Status:** Accepted

**Date:** 2026-07-17

---

# Context

JARVIS originally distinguished between external knowledge and active mission execution.

As the architecture matured, additional concepts emerged:

- Mission Journal
- After Action Review (AAR)
- Mission Executive Summary
- Operational Fingerprint
- Mission Package (`.jmp`)
- Archive Manager
- Experience Assimilation

Initially these concepts were collectively described as an "Experience Engine."

Further architectural analysis demonstrated that this abstraction was too narrow.

These components do not merely process experience.

Together they define how JARVIS remembers, preserves, reflects upon, and reuses operational experience across its lifetime.

This constitutes a persistent architectural domain comparable in importance to the Knowledge Engine.

---

# Decision

JARVIS shall recognize **Operational Memory** as a first-class architectural domain.

Operational Memory is responsible for preserving, organizing, consolidating, retrieving, and applying operational experience.

Operational Memory is distinct from, but complementary to, the Knowledge Engine.

---

# Architectural Responsibilities

Operational Memory encompasses, but is not limited to:

- Mission Journals
- After Action Reviews
- Mission Executive Summaries
- Operational Fingerprints
- Mission Packages (`.jmp`)
- Archive Management
- Experience Assimilation
- Experience Graphs
- Historical Mission Retrieval
- Operational Replay
- Experience Reuse

Future capabilities related to episodic memory, mission replay, case-based reasoning, or historical learning shall belong to this architectural domain unless a stronger architectural justification exists elsewhere.

---

# Relationship to the Knowledge Engine

The Knowledge Engine manages externally acquired knowledge.

Operational Memory manages internally acquired experience.

The two systems are complementary.

Knowledge answers:

> What is known about the world?

Operational Memory answers:

> What has JARVIS experienced?

Judgment is expected to emerge through the disciplined combination of both.

---

# Memory Hierarchy

The architectural memory model consists of multiple complementary forms of memory.

## Working Memory

Represents active Mission state.

Maintained by Mission Lifecycle.

Answers:

> What is happening now?

---

## Operational Memory

Represents completed operational experience.

Maintained through Mission Journals, AARs, Mission Packages, and archival services.

Answers:

> What have we learned through experience?

---

## Knowledge Memory

Represents externally acquired, verified knowledge.

Maintained by the Knowledge Engine.

Answers:

> What does verified evidence tell us?

---

## Procedural Memory

Represents capabilities, workflows, policies, and operational procedures available to JARVIS.

Answers:

> What am I capable of doing?

---

# Experience Consolidation

Operational experience shall not automatically become reusable knowledge.

Experience shall progress through a structured lifecycle:

Mission Execution

↓

Mission Journal

↓

After Action Review

↓

Lesson Candidates

↓

Validation

↓

Experience Assimilation

↓

Operational Memory

↓

Future Mission Reuse

Every reusable lesson shall remain traceable to its originating Mission and supporting evidence.

---

# Architectural Principles

Operational Memory shall preserve:

- provenance,
- historical context,
- uncertainty,
- confidence,
- contradictions,
- review history,
- applicability conditions.

Operational Memory shall not rewrite historical decisions using information that became available only later.

Historical understanding must remain historically accurate.

---

# Archive Philosophy

Completed Missions are never discarded solely because they become inactive.

Inactive Missions transition into compressed Mission Packages.

Compressed Missions remain discoverable through:

- Mission Executive Summaries,
- Operational Fingerprints,
- structured archive metadata,
- normalized tags,
- validated lessons.

Full restoration occurs only when operationally justified.

---

# Consequences

Adopting Operational Memory as a first-class architectural domain provides:

- clear separation between knowledge and experience,
- traceable operational learning,
- long-term institutional memory,
- scalable archival architecture,
- reusable operational judgment,
- evidence-based reflection,
- consistent historical provenance,
- future support for episodic recall and case-based reasoning.

It also establishes a stable conceptual framework that is independent of any particular language model, storage implementation, or execution platform.

---

# Guiding Doctrine

Knowledge describes reality.

Operational Memory describes experience.

Planning determines intent.

Execution produces evidence.

Reflection extracts lessons.

Judgment emerges from the disciplined integration of verified knowledge and accumulated operational experience.

---

# Design Principles

Knowledge is permanent.

Intelligence is upgradable.

Experience is cumulative.

Judgment is earned.

# JARVIS Operational Context Architecture

Document ID: UI-0004

Status: Draft

Version: 1.0

Program: Mission Control Architecture

Phase: VIII-A3

---

# 1. Purpose

Operational Context is the architectural layer that gives JARVIS a persistent
understanding of operational work.

Unlike traditional AI assistants, JARVIS does not organize work around chat
sessions.

Instead, every action belongs to a persistent operational hierarchy.

Operational Context answers five questions at every moment.

• What Mission is active?

• What Objective is active?

• What Task is active?

• What Activity is occurring?

• What Command initiated the Activity?

Operational Context becomes the authoritative source of continuity for the
entire JARVIS platform.

Conversations are interfaces.

Operational Context is operational truth.

---

# 2. Design Goals

The Operational Context subsystem shall:

• persist across application restarts,

• persist across operating systems,

• persist across devices,

• survive interrupted sessions,

• support autonomous execution,

• support operator-driven execution,

• support multiple Directors,

• support future expansion.

Operational Context exists independently from the user interface.

Mission Control displays Operational Context.

Mission Control does not own Operational Context.

---

# 3. Canonical Operational Hierarchy

Every operation performed by JARVIS belongs to exactly one canonical
operational hierarchy.

Mission
    ↓
Objective
    ↓
Task
    ↓
Activity
    ↓
Command

Each level narrows operational scope.

Every child belongs to one parent.

No child exists independently.

This hierarchy is the operational truth of JARVIS.

The user interface presents this hierarchy.

It never owns it.

---

# 4. Mission

Mission is the highest operational unit.

Every Mission answers one question.

Why does this work exist?

Examples:

• Build Mission Control

• Improve Knowledge Engine

• Develop Voice Director

• Acquire Medical Knowledge

• Secure Home Infrastructure

A Mission may span:

• multiple weeks,

• multiple operating systems,

• multiple devices,

• multiple user sessions,

• multiple Directors.

A Mission survives:

• application restarts,

• operating-system changes,

• hardware replacement,

• user-interface redesign.

A Mission is never equivalent to a conversation.

Conversation is merely one interface into the Mission.

---

# 5. Mission Responsibilities

Every Mission defines:

• purpose,

• operational scope,

• success criteria,

• lifecycle,

• associated Objectives,

• associated artifacts,

• responsible Director,

• completion conditions.

Mission provides the highest level of operational context.

Every subordinate object derives meaning from its parent Mission.

---

# 6. Mission Ownership

Every Mission has exactly one authoritative owner.

Normally this owner is the Executive Director.

Other Directors contribute work.

They do not redefine Mission purpose.

Mission ownership determines:

• planning,

• authorization,

• scheduling,

• reporting,

• completion.

Mission ownership may change only through explicit operational events.

Historical ownership shall always remain available.


---

# 7. Objectives

Objectives divide a Mission into major operational accomplishments.

An Objective answers the question:

"What significant outcome must be achieved to complete this Mission?"

Examples

Mission

Build Mission Control

Objectives

• Navigation Architecture

• Operational Context

• Commander Brief

• SITREP

• API Design

• Frontend Implementation

Objectives should remain stable throughout Mission execution.

Objectives should describe outcomes rather than implementation details.

Objectives belong to exactly one Mission.

Objectives never exist independently.

---

# 8. Objective Responsibilities

Every Objective defines:

• expected outcome,

• associated Tasks,

• completion criteria,

• operational priority,

• current status,

• associated artifacts.

Objectives provide planning structure.

They do not directly execute work.

---

# 9. Tasks

Tasks are the primary operational work units.

A Task answers:

"What concrete work must now be performed?"

Examples

• Write Operational Context specification

• Review Navigation Architecture

• Execute verification suite

• Merge feature branch

• Download NIST publications

Tasks should normally produce one measurable result.

Large Tasks should be divided into smaller Tasks.

Tasks belong to exactly one Objective.

---

# 10. Task Responsibilities

Every Task records:

• owner,

• start time,

• completion time,

• current status,

• associated Activities,

• produced artifacts,

• blocking conditions,

• completion result.

Tasks represent planned work.

Activities represent current execution.

---

# 11. Activities

Activities describe what is happening right now.

Examples

Writing documentation

Running tests

Downloading sources

Embedding documents

Waiting for approval

Reviewing evidence

Activities are temporary.

Tasks are persistent.

A Task may contain many Activities throughout its lifetime.

Normally only one Activity is active at a time.

---

# 12. Activity Responsibilities

Activities maintain:

• execution status,

• timestamps,

• associated Commands,

• execution environment,

• produced events,

• generated logs,

• temporary execution metadata.

Activities are not planning objects.

Activities are execution objects.


---

# 13. Commands

Commands are the smallest explicit operational instruction recognized by
JARVIS.

A Command answers the question:

"What action should now be performed?"

Examples

• Run verification.

• Continue previous Mission.

• Pause current research.

• Open the latest SITREP.

• Acquire approved publications.

Commands may originate from:

• keyboard input,

• voice input,

• Mission Control,

• scheduled automation,

• Director delegation,

• external integrations.

Commands belong to exactly one Activity.

Commands never redefine Mission structure.

---

# 14. Command Responsibilities

Every Command records:

• issuing actor,

• execution time,

• execution status,

• execution target,

• associated Activity,

• generated events,

• execution result.

Commands should always be traceable.

No Command should exist without operational context.

---

# 15. Operational Context Ownership

Operational Context is owned by backend services.

Mission Control visualizes Operational Context.

Mission Control never becomes the authoritative owner.

The Executive Director coordinates Mission state.

Individual Directors contribute execution state.

No subsystem may silently redefine Mission ownership.

Operational Context is shared across the entire platform.

---

# 16. Context Persistence

Operational Context survives:

• application restart,

• operating-system restart,

• hardware restart,

• temporary network interruption,

• user-interface replacement.

Operational Context is stored independently from the frontend.

Every supported device accesses the same authoritative operational state.

---

# 17. Context Restoration

During startup JARVIS restores:

Mission

↓

Objective

↓

Task

↓

Activity

↓

Recent Command

If restoration cannot continue, JARVIS restores the highest valid context
available.

JARVIS never invents missing context.


---

# 18. Foreground Mission

JARVIS may manage many Missions simultaneously.

Only one Mission is considered the foreground Mission for a given operator.

The foreground Mission represents the primary operational focus.

General continuation commands such as:

Continue.

Resume work.

Open current task.

Resume yesterday's work.

shall resolve against the foreground Mission unless the operator explicitly
selects another Mission.

Changing the foreground Mission is an operational event.

Foreground changes should be recorded.

---

# 19. Background Missions

Background Missions continue operating while another Mission is active.

Examples include:

• knowledge acquisition,

• scheduled research,

• indexing,

• synchronization,

• device monitoring,

• integrity verification.

Background Missions remain visible through Mission Control and SITREP.

Background execution never replaces the foreground Mission.

---

# 20. Context Switching

Switching operational context must always be explicit.

Every context switch records:

• previous Mission,

• new Mission,

• timestamp,

• initiating actor,

• reason.

High-impact context switches should require confirmation.

Silent context switching is prohibited.

---

# 21. Mission Journal

Mission Journal records the history of Operational Context.

Mission Journal includes:

• Mission creation,

• Objective activation,

• Task completion,

• Activity transitions,

• Commands,

• approvals,

• failures,

• retries,

• Mission completion.

Mission Journal is historical.

Operational Context represents current state.

Neither replaces the other.

---

# 22. Commander Brief Relationship

Commander Brief is generated from Operational Context.

Operational Context provides:

• active Mission,

• active Objective,

• active Task,

• interrupted Activity,

• recent Command,

• recommended continuation.

Commander Brief summarizes Operational Context.

Commander Brief never becomes the authoritative source of Mission state.


---

# 23. SITREP Relationship

Situation Reports are generated from authoritative operational state.

Each SITREP item should identify:

• associated Mission,

• associated Objective,

• associated Task,

• originating Activity,

• severity,

• recommended action.

SITREP summarizes operational events.

SITREP does not replace Operational Context.

---

# 24. Multi-Device Operation

Operational Context must remain consistent across every supported device.

Examples include:

• desktop,

• laptop,

• mobile,

• Raspberry Pi,

• Meta Quest.

Different devices may present different interfaces.

They shall present the same operational truth.

---

# 25. Backend Responsibilities

Backend services own:

• Mission state,

• Objective state,

• Task state,

• Activity state,

• lifecycle,

• persistence,

• restoration,

• authorization.

Backend services are the authoritative source of Operational Context.

---

# 26. Frontend Responsibilities

Mission Control owns presentation only.

Mission Control may control:

• layout,

• window state,

• selected panels,

• visual themes,

• local display preferences.

Mission Control never owns operational state.

---

# 27. Architectural Rules

The following rules are mandatory.

• Every Command belongs to an Activity.

• Every Activity belongs to a Task.

• Every Task belongs to an Objective.

• Every Objective belongs to a Mission.

• Operational Context survives restart.

• Mission Control visualizes Operational Context.

• Conversations never become Mission identity.

• Silent Mission switching is prohibited.

• Missing context shall never be invented.

---

# 28. Future Expansion

Operational Context is designed to support future capabilities including:

• Commander Brief,

• SITREP,

• Mission Journal,

• Voice Director,

• Vision Director,

• Meta Quest,

• Raspberry Pi,

• autonomous execution,

• collaborative execution,

• multi-user environments.

Future capabilities extend Operational Context.

They do not replace it.

---

# 29. Acceptance Criteria

Operational Context architecture is considered complete when:

✓ Mission is the highest operational entity.

✓ Every child has one parent.

✓ Context survives restart.

✓ Context survives device changes.

✓ Mission ownership is explicit.

✓ Frontend and backend ownership remain separated.

✓ Commander Brief derives from Operational Context.

✓ SITREP derives from Operational Context.

✓ Mission Journal records Operational Context history.

✓ Operational Context remains the authoritative source of operational truth.

---

# 30. Architectural Conclusion

Operational Context defines how JARVIS understands work.

Rather than organizing execution around conversations, JARVIS organizes
execution around Missions.

Mission

↓

Objective

↓

Task

↓

Activity

↓

Command

This hierarchy provides persistent operational continuity across devices,
sessions, Directors, and future execution environments.

Operational Context is therefore a foundational architectural subsystem of
JARVIS and serves as the operational backbone of Mission Control.


---

# 17. Awaiting Approval

A Mission enters awaiting_approval when further progress requires an explicit
operator or authorized authority decision.

Examples include:

• approving a proposed action,

• granting access to an external system,

• accepting operational risk,

• authorizing resource consumption,

• approving acquisition from a new source,

• authorizing a destructive or irreversible action.

The approval request must identify:

• requested action,

• operational purpose,

• affected Mission,

• affected Objective or Task,

• expected benefit,

• known risk,

• available alternatives,

• requesting actor,

• expiration or urgency when applicable.

Awaiting approval is not equivalent to blocked.

A blocked Mission cannot progress because of an impediment.

A Mission awaiting approval can progress once an authorized decision is made.

---

# 18. Mission Completion

A Mission is completed when its defined success criteria have been satisfied.

Completion must be based upon Mission outcomes rather than the absence of
running Tasks.

A Mission may be completed only when:

• required Objectives are complete,

• required artifacts exist,

• required verification has passed,

• unresolved failures are accepted or resolved,

• required approvals are complete,

• completion criteria are satisfied.

Completion should record:

• completion timestamp,

• final outcome,

• completed Objectives,

• unresolved follow-up items,

• generated artifacts,

• verification summary,

• completing actor.

---

# 19. Mission Success Criteria

Every Mission should define success criteria during planning.

Success criteria should be:

• understandable,

• reviewable,

• relevant to Mission purpose,

• measurable when practical,

• independent of superficial activity counts.

Examples of weak success criteria include:

• many files created,

• many Commands executed,

• a long conversation completed.

Examples of stronger success criteria include:

• architecture approved and committed,

• source registry verified,

• required publications acquired and validated,

• system restored to healthy operation,

• operator decision completed with supporting evidence.

Mission progress must not be confused with Mission success.

---

# 20. Partial Completion

A Mission may reach partial completion when some intended outcomes are achieved
but full success criteria are not satisfied.

Partial completion should identify:

• completed outcomes,

• incomplete outcomes,

• unresolved blockers,

• accepted limitations,

• recommended continuation,

• whether a follow-up Mission is required.

Partial completion must not be silently reported as complete.

The operator must be able to distinguish complete, partially complete, and
failed outcomes.

---

# 21. Mission Failure

A Mission enters failed when its intended outcome cannot be achieved under the
current plan, authorization, resources, or constraints.

Failure must record:

• failure timestamp,

• failure reason,

• affected Objectives,

• failed Tasks or Activities,

• last valid Operational Context,

• partial artifacts,

• known recovery options,

• retry eligibility.

Failure does not erase Mission history.

Failure does not automatically imply that all produced work is unusable.

---

# 22. Failure Classification

Mission failure may be classified as:

• recoverable,

• non-recoverable,

• policy-rejected,

• authorization-denied,

• resource-exhausted,

• dependency-failed,

• integrity-failed,

• operator-terminated,

• unknown.

Failure classification supports:

• Commander Brief summaries,

• SITREP severity,

• retry decisions,

• Mission Journal accuracy,

• future planning.

Unknown failure should remain unknown until evidence supports a stronger
classification.

---

# 23. Mission Recovery

A failed or blocked Mission may enter a recovery workflow.

Recovery should identify:

• highest valid Mission state,

• preserved Objectives,

• preserved Tasks,

• reusable artifacts,

• failed assumptions,

• changed dependencies,

• required approval,

• recommended recovery plan.

Recovery must not erase the original failure.

A recovery attempt should be recorded as a new execution attempt or revised
plan within the same Mission when the Mission purpose remains unchanged.

---

# 24. Mission Retry

A retry is appropriate when:

• Mission purpose remains valid,

• failure cause is understood or meaningfully changed,

• required authorization remains valid,

• recovery is technically possible,

• retry risk is acceptable.

A retry should record:

• previous failure,

• retry reason,

• changed inputs,

• changed plan,

• initiating actor,

• attempt number,

• expected improvement.

Repeated retries without meaningful change should be prevented or escalated.

---

# 25. Mission Cancellation

A Mission enters cancelled when an authorized actor intentionally ends it
before completion.

Cancellation must record:

• cancelling actor,

• reason,

• timestamp,

• active Operational Context,

• affected background work,

• preserved artifacts,

• cleanup requirements.

Cancellation must define whether subordinate work is:

• terminated,

• allowed to finish,

• transferred,

• preserved for later recovery.

Cancellation is not equivalent to failure.

---

# 26. Mission Archival

A completed, failed, or cancelled Mission may be archived.

Archival removes the Mission from active operational views while preserving:

• Mission identity,

• Mission Journal,

• lifecycle history,

• Objectives,

• Tasks,

• decisions,

• approvals,

• artifacts,

• verification results,

• failure records.

Archival is an information-management action.

It must not rewrite Mission outcomes.

---

# 27. Mission Reopening

An archived Mission may be reopened only when continued work remains part of
the original Mission purpose.

Reopening should record:

• reopening actor,

• reason,

• restored state,

• new or revised Objectives,

• authorization review,

• timestamp.

If the desired work represents a materially different purpose, JARVIS should
create a new Mission and link it to the archived Mission.

Reopening must not erase the original completion, failure, or cancellation
record.


---

# 28. Foreground Mission

JARVIS may manage multiple Missions concurrently.

Only one Mission is normally designated as the foreground Mission for a given
operator session.

The foreground Mission determines:

• default command context,

• primary Objective display,

• current Task emphasis,

• relevant artifacts,

• recommended next action,

• Mission Workspace focus.

Changing the foreground Mission is an explicit lifecycle event.

---

# 29. Background Missions

Background Missions may continue executing while another Mission remains in
the foreground.

Examples include:

• knowledge acquisition,

• indexing,

• synchronization,

• scheduled research,

• device monitoring,

• integrity verification.

Background Missions must remain visible through:

• Mission Control,

• Commander Brief,

• SITREP,

• Mission switcher,

• Mission Journal.

Background execution must not silently replace the foreground Mission.

---

# 30. Mission Relationships

Missions may be related without sharing identity.

Supported conceptual relationships include:

• depends_on,

• supports,

• follows,

• supersedes,

• duplicates,

• conflicts_with,

• derived_from,

• related_to.

Mission relationships must be explicit.

Relationship metadata must not redefine lifecycle state.

---

# 31. Parent and Child Missions

A complex Mission may create subordinate child Missions when:

• work requires independent authorization,

• work requires a different owner,

• work spans a separate operational domain,

• work requires isolated lifecycle management,

• work has distinct completion criteria.

A child Mission must retain a link to its parent Mission.

A parent Mission must not silently absorb child Mission outcomes.

Child Missions remain independently reviewable.

---

# 32. Mission Dependencies

A Mission may depend upon:

• another Mission,

• an Objective,

• an external system,

• a device,

• a trusted source,

• an approval,

• a scheduled time,

• a required capability.

Dependencies must identify:

• dependency type,

• dependency state,

• affected Mission,

• expected resolution,

• blocking impact.

Unresolved dependencies may place a Mission in waiting or blocked state.

---

# 33. Mission Ownership

Every Mission has one authoritative owner.

The owner may be:

• the Executive Director,

• an authorized operator,

• a specialized Director under Executive coordination,

• an approved automation service,

• an external coordinating system.

Ownership determines responsibility for:

• planning,

• lifecycle transitions,

• delegation,

• reporting,

• completion review,

• archival.

Ownership changes must be explicit and auditable.

---

# 34. Director Participation

Directors may contribute to a Mission without owning it.

Director participation may include:

• planning,

• Task execution,

• evidence collection,

• verification,

• recommendation,

• monitoring,

• recovery.

No Director may silently redefine Mission purpose or success criteria.

Cross-Director Mission changes require coordinated state updates.

---

# 35. Lifecycle Transition Rules

Mission lifecycle transitions must be controlled.

Examples of valid transitions include:

proposed -> planned

planned -> ready

ready -> active

active -> waiting

active -> paused

active -> blocked

active -> awaiting_approval

waiting -> active

paused -> active

blocked -> active

awaiting_approval -> active

active -> completed

active -> failed

active -> cancelled

completed -> archived

failed -> archived

cancelled -> archived

archived -> planned

Invalid transitions must be rejected or explicitly repaired.

---

# 36. Transition Validation

Before applying a lifecycle transition, JARVIS should validate:

• current Mission state,

• requested target state,

• initiating actor,

• authorization,

• blocking conditions,

• required approvals,

• state invariants,

• transition reason.

A transition must not be accepted merely because the frontend requested it.

The backend owns lifecycle validity.

---

# 37. Mission State Invariants

The following invariants should remain true:

• completed Missions do not contain running Tasks,

• archived Missions do not execute new Commands,

• cancelled Missions do not silently resume,

• failed Missions preserve failure evidence,

• active Missions have valid Operational Context,

• foreground Mission identity is explicit,

• lifecycle history is append-only,

• authorization state remains independently reviewable.

Broken invariants require repair or degraded-state handling.

---

# 38. Lifecycle Events

Every meaningful lifecycle change should emit a normalized event.

Examples include:

• mission.proposed,

• mission.planned,

• mission.ready,

• mission.activated,

• mission.waiting,

• mission.paused,

• mission.blocked,

• mission.approval_requested,

• mission.completed,

• mission.failed,

• mission.cancelled,

• mission.archived,

• mission.reopened,

• mission.foreground_changed,

• mission.owner_changed,

• mission.dependency_changed.

Events describe what changed.

State describes the current authoritative condition.

---

# 39. Event Requirements

A Mission lifecycle event should identify:

• event identifier,

• Mission identifier,

• event type,

• previous state,

• new state,

• initiating actor,

• timestamp,

• reason,

• related Objective or Task when relevant,

• correlation identifier,

• causation identifier.

Lifecycle events must be traceable.

---

# 40. Mission Journal Relationship

The Mission Journal records Mission lifecycle history.

Each lifecycle event should be represented directly or through a normalized
journal entry.

The Mission Journal answers:

• what changed,

• when it changed,

• who initiated it,

• why it changed,

• what resulted.

Mission Journal is historical.

Mission state is current.

---

# 41. SITREP Relationship

SITREP communicates lifecycle changes that matter now.

Examples include:

• Mission blocked,

• approval required,

• Mission failed,

• Mission completed,

• background Mission changed state,

• dependency resolved.

Not every lifecycle event belongs in SITREP.

SITREP should surface only operationally meaningful changes.

---

# 42. Commander Brief Relationship

Commander Brief summarizes relevant lifecycle state at session start.

It may include:

• foreground Mission,

• paused Missions,

• blocked Missions,

• Missions awaiting approval,

• recently completed Missions,

• failed Missions requiring review.

Commander Brief must derive Mission status from authoritative lifecycle state.

---

# 43. Startup Recovery

At startup, JARVIS should reconcile Mission lifecycle state before presenting
Mission Control.

Recovery should identify:

• Missions marked active before shutdown,

• interrupted Tasks,

• stale worker state,

• unresolved approvals,

• incomplete transitions,

• missing dependencies,

• inconsistent foreground state.

Recovered state must not be fabricated.

---

# 44. Stale Mission Detection

A Mission may be considered stale when:

• it has remained active without meaningful events,

• its owner is unavailable,

• required dependencies no longer exist,

• its authorization has expired,

• its foreground status conflicts with another session,

• its Operational Context cannot be restored.

Stale does not automatically mean failed.

JARVIS should report stale state and recommend review.

---

# 45. Lifecycle Security

Lifecycle operations must respect:

• operator identity,

• role,

• Mission authorization,

• device trust,

• capability restrictions,

• external-system policy,

• audit requirements.

Unauthorized users or devices must not activate, cancel, reopen, archive, or
change ownership of a Mission.

---

# 46. Architectural Rules

The following rules are mandatory.

• Mission is the primary organizational unit of JARVIS.

• Mission identity remains stable.

• Lifecycle state is authoritative backend state.

• Foreground Mission changes are explicit.

• Background Missions remain visible.

• Mission relationships are explicit.

• Dependencies are reviewable.

• Ownership is singular and auditable.

• Directors may contribute without silently redefining Mission purpose.

• Transitions are validated.

• Lifecycle history is preserved.

• Events describe changes.

• State describes current truth.

• Failure, cancellation, and archival remain distinct.

---

# 47. Acceptance Criteria

Mission Lifecycle architecture is complete when:

✓ Mission creation is deliberate,

✓ Mission authorization is separate from execution,

✓ canonical Mission states are defined,

✓ valid transitions are controlled,

✓ foreground and background Missions are distinct,

✓ parent and child Missions remain traceable,

✓ dependencies are explicit,

✓ ownership is authoritative and auditable,

✓ failures preserve evidence,

✓ retries preserve prior attempts,

✓ completion derives from success criteria,

✓ archival preserves history,

✓ startup recovery reconciles lifecycle state,

✓ Commander Brief, SITREP, and Mission Journal consume lifecycle state without
  replacing it.

---

# 48. Architectural Conclusion

Mission Lifecycle defines how purposeful work moves through JARVIS from
recognition of intent to historical preservation.

A Mission may be proposed, planned, authorized, activated, paused, blocked,
resumed, completed, failed, cancelled, archived, or reopened.

Every transition carries operational meaning.

Every transition remains traceable.

Mission Lifecycle provides the authoritative structure required by Operational
Context, Commander Brief, Mission Workspace, SITREP, Mission Journal, state
contracts, event architecture, and future autonomous execution.

Mission is therefore the primary organizational unit of JARVIS.

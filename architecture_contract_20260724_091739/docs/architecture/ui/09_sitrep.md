# JARVIS Mission Control
# SITREP Architecture

Status: Architecture Definition
Phase: VIII-A8
Document: 09_sitrep.md
Authority: Mission Control Architecture

Depends On:

- 00_design_language.md
- 01_user_experience.md
- 02_screen_architecture.md
- 03_navigation_model.md
- 04_operational_context.md
- 05_commander_brief.md
- 06_mission_workspace.md
- 07_operator_experience.md
- 08_mission_lifecycle.md

---

# 1. Purpose

This document defines the architecture of the JARVIS Situation Report,
hereafter referred to as SITREP.

SITREP is the operational intelligence layer of Mission Control.

Its purpose is to transform authoritative operational state into concise,
actionable awareness for the operator.

SITREP answers five questions:

• What changed?

• Why does it matter?

• Does it require action?

• What action is recommended?

• What happens if no action is taken?

SITREP derives information from authoritative services.

It never becomes an authoritative source itself.

---

# 2. Governing Principle

SITREP communicates only what matters now.

Not everything that happens deserves operator attention.

JARVIS must distinguish between:

• an event,

• a state change,

• an operational consequence,

• an operator decision.

Only the latter two normally belong in SITREP.

---

# 3. Architectural Doctrine

Mission state remains authoritative.

Mission Journal preserves history.

Events describe change.

Commander Brief restores continuity.

SITREP communicates present operational significance.

Each serves a different purpose.

None replaces another.

---

# 4. SITREP Definition

A SITREP is a normalized operational assessment derived from one or more
authoritative sources.

A SITREP item represents something whose current operational significance
justifies operator awareness.

A SITREP item may represent:

• Mission state,

• approval request,

• dependency,

• failure,

• completion,

• degraded capability,

• integrity concern,

• recommendation,

• security issue,

• required operator decision.

SITREP items communicate meaning rather than raw events.

---

# 5. What SITREP Is Not

SITREP is not:

• an activity feed,

• a notification center,

• a log viewer,

• a Director transcript,

• a debugging console,

• a telemetry dashboard,

• an audit log.

Those capabilities remain available elsewhere.

SITREP exists to summarize operational significance.

---

# 6. Relationship to Mission Lifecycle

Mission Lifecycle defines the current authoritative Mission state.

SITREP derives operational meaning from lifecycle transitions.

Examples include:

• Mission activated,

• Mission blocked,

• Mission awaiting approval,

• Mission completed,

• Mission failed,

• Mission recovered,

• Mission archived.

Not every lifecycle transition produces a SITREP item.

Operational relevance determines presentation.

---

# 7. Relationship to Commander Brief

Commander Brief provides startup orientation.

SITREP provides ongoing operational awareness.

Commander Brief may summarize unresolved or recently important SITREP items.

SITREP continues evolving throughout the session.

Relationship:

    SITREP
        │
        │ unresolved operational items
        ▼
 Commander Brief

The Commander Brief should never duplicate the complete SITREP stream.

---

# 8. Relationship to Mission Journal

Mission Journal records durable Mission history.

SITREP represents temporary operational attention.

A Mission Journal entry may remain forever.

A SITREP item may disappear after:

• acknowledgement,

• resolution,

• supersession,

• expiration,

• Mission archival.

History remains.

Attention moves on.

---

# 9. Relationship to Events

Events describe individual changes.

SITREP derives meaning from groups of events combined with Mission state.

One event may produce:

• no SITREP,

• one SITREP,

• an update to an existing SITREP.

Multiple events may become one operational statement.

SITREP reduces noise.

It does not amplify it.

---

# 10. Relationship to Operational Context

Operational Context determines whether an event matters.

The same event may have different significance depending upon:

• foreground Mission,

• active Objective,

• operator role,

• Mission priority,

• current dependencies,

• authorization,

• current execution state.

Operational Context gives SITREP meaning.

---

# 11. Source Authority

SITREP must never become the source of truth.

Mission state belongs to Mission services.

Approvals belong to authorization services.

Evidence belongs to evidence management.

Capability health belongs to diagnostics.

Security belongs to security services.

SITREP summarizes.

It never replaces authoritative state.

---

# 12. Governing Rule

Every SITREP item must answer:

Why does this matter now?

If that question cannot be answered, the information probably belongs in:

• Events,

• Mission Journal,

• Diagnostics,

• Audit,

or another subsystem rather than SITREP.


---

# 13. SITREP Item Structure

Every SITREP item should contain sufficient information for an operator to
understand the operational condition without consulting implementation details.

A canonical SITREP item should contain:

• SITREP identifier,

• Mission identifier,

• title,

• summary,

• operational significance,

• category,

• priority,

• current status,

• recommended action,

• required action when applicable,

• consequence of inaction when known,

• creation timestamp,

• last update timestamp,

• related Objective,

• related Task,

• source references,

• correlation identifier.

Optional information may include:

• confidence,

• assigned operator,

• affected Director,

• affected capability,

• evidence references,

• deadline,

• recovery recommendation.

---

# 14. Title

A SITREP title identifies the operational condition.

Titles should be concise, specific, and understandable.

Weak titles include:

• Error

• Update

• Task Changed

• Warning

• Notification

Stronger titles include:

• Knowledge Acquisition Blocked

• Source Approval Required

• Mission Ready For Review

• Engineering Verification Complete

• Runtime Storage Capacity Degraded

The title should identify the condition rather than the event.

---

# 15. Summary

The summary explains the current operational situation.

It should normally answer:

• what changed,

• which Mission is affected,

• current consequence,

• immediate relevance.

The summary should avoid:

• stack traces,

• implementation details,

• unexplained identifiers,

• unnecessary technical language,

• unsupported conclusions.

Additional evidence should remain available through progressive disclosure.

---

# 16. Operational Significance

Every SITREP item must answer:

Why does this matter?

Examples include:

• Mission progress stopped,

• operator approval required,

• integrity verification failed,

• dependency restored,

• completion criteria satisfied,

• security posture changed,

• evidence became available,

• recovery may begin,

• recommended action available.

Operational significance distinguishes SITREP from raw events.

---

# 17. Categories

Canonical SITREP categories include:

• Mission,

• Approval,

• Recommendation,

• Dependency,

• Completion,

• Failure,

• Security,

• System Health,

• Capability,

• Evidence,

• Risk,

• Operator Action.

Categories organize information.

Categories do not determine priority.

---

# 18. Priority

Canonical priorities are:

• Critical

• High

• Normal

• Low

• Informational

Priority represents operational consequence rather than technical severity.

A technically serious condition may have little operational consequence.

Likewise, a simple approval request may become High priority if it blocks the
foreground Mission.

---

# 19. Critical Priority

Critical indicates immediate operational consequence.

Examples include:

• destructive action,

• confirmed security compromise,

• irreversible data loss,

• Mission integrity failure,

• active corruption,

• widespread service failure,

• immediate safety concern.

Critical should interrupt normal workflow only when interruption is justified.

Critical must never become routine.

---

# 20. High Priority

High priority represents significant impact to active work.

Examples include:

• foreground Mission blocked,

• approval required,

• repeated execution failure,

• dependency unavailable,

• verification failure,

• imminent deadline risk.

High-priority items should remain visible until resolved.

---

# 21. Normal Priority

Normal priority represents meaningful operational awareness.

Examples include:

• Mission entered review,

• dependency restored,

• significant artifact produced,

• background work completed,

• recommendation available.

Normal should be the default priority.

---

# 22. Low and Informational Priority

Low priority represents minor operational importance.

Informational represents awareness without expected action.

Examples include:

• scheduled synchronization completed,

• maintenance finished,

• optional capability restored,

• archival completed.

Informational items should not accumulate indefinitely.

They may be grouped or automatically expire.

---

# 23. Actionability

Every SITREP item should identify one of four conditions:

• action required,

• review recommended,

• awareness only,

• automatically resolving.

If action is required, the expected action should be explicit.

Examples include:

• approve,

• reject,

• inspect,

• retry,

• assign,

• pause,

• resume,

• acknowledge risk,

• reopen Mission.

JARVIS should never imply action where no meaningful action exists.

---

# 24. Recommended Action

JARVIS may recommend an action.

Recommendations should identify:

• proposed action,

• reason,

• expected benefit,

• known risk,

• alternatives when appropriate,

• required authorization.

Recommendations assist operator judgment.

They do not replace operator judgment.


---

# 13. SITREP Item Structure

Every SITREP item should contain sufficient information for an operator to
understand the operational condition without consulting implementation details.

A canonical SITREP item should contain:

• SITREP identifier,

• Mission identifier,

• title,

• summary,

• operational significance,

• category,

• priority,

• current status,

• recommended action,

• required action when applicable,

• consequence of inaction when known,

• creation timestamp,

• last update timestamp,

• related Objective,

• related Task,

• source references,

• correlation identifier.

Optional information may include:

• confidence,

• assigned operator,

• affected Director,

• affected capability,

• evidence references,

• deadline,

• recovery recommendation.

---

# 14. Title

A SITREP title identifies the operational condition.

Titles should be concise, specific, and understandable.

Weak titles include:

• Error

• Update

• Task Changed

• Warning

• Notification

Stronger titles include:

• Knowledge Acquisition Blocked

• Source Approval Required

• Mission Ready For Review

• Engineering Verification Complete

• Runtime Storage Capacity Degraded

The title should identify the condition rather than the event.

---

# 15. Summary

The summary explains the current operational situation.

It should normally answer:

• what changed,

• which Mission is affected,

• current consequence,

• immediate relevance.

The summary should avoid:

• stack traces,

• implementation details,

• unexplained identifiers,

• unnecessary technical language,

• unsupported conclusions.

Additional evidence should remain available through progressive disclosure.

---

# 16. Operational Significance

Every SITREP item must answer:

Why does this matter?

Examples include:

• Mission progress stopped,

• operator approval required,

• integrity verification failed,

• dependency restored,

• completion criteria satisfied,

• security posture changed,

• evidence became available,

• recovery may begin,

• recommended action available.

Operational significance distinguishes SITREP from raw events.

---

# 17. Categories

Canonical SITREP categories include:

• Mission,

• Approval,

• Recommendation,

• Dependency,

• Completion,

• Failure,

• Security,

• System Health,

• Capability,

• Evidence,

• Risk,

• Operator Action.

Categories organize information.

Categories do not determine priority.

---

# 18. Priority

Canonical priorities are:

• Critical

• High

• Normal

• Low

• Informational

Priority represents operational consequence rather than technical severity.

A technically serious condition may have little operational consequence.

Likewise, a simple approval request may become High priority if it blocks the
foreground Mission.

---

# 19. Critical Priority

Critical indicates immediate operational consequence.

Examples include:

• destructive action,

• confirmed security compromise,

• irreversible data loss,

• Mission integrity failure,

• active corruption,

• widespread service failure,

• immediate safety concern.

Critical should interrupt normal workflow only when interruption is justified.

Critical must never become routine.

---

# 20. High Priority

High priority represents significant impact to active work.

Examples include:

• foreground Mission blocked,

• approval required,

• repeated execution failure,

• dependency unavailable,

• verification failure,

• imminent deadline risk.

High-priority items should remain visible until resolved.

---

# 21. Normal Priority

Normal priority represents meaningful operational awareness.

Examples include:

• Mission entered review,

• dependency restored,

• significant artifact produced,

• background work completed,

• recommendation available.

Normal should be the default priority.

---

# 22. Low and Informational Priority

Low priority represents minor operational importance.

Informational represents awareness without expected action.

Examples include:

• scheduled synchronization completed,

• maintenance finished,

• optional capability restored,

• archival completed.

Informational items should not accumulate indefinitely.

They may be grouped or automatically expire.

---

# 23. Actionability

Every SITREP item should identify one of four conditions:

• action required,

• review recommended,

• awareness only,

• automatically resolving.

If action is required, the expected action should be explicit.

Examples include:

• approve,

• reject,

• inspect,

• retry,

• assign,

• pause,

• resume,

• acknowledge risk,

• reopen Mission.

JARVIS should never imply action where no meaningful action exists.

---

# 24. Recommended Action

JARVIS may recommend an action.

Recommendations should identify:

• proposed action,

• reason,

• expected benefit,

• known risk,

• alternatives when appropriate,

• required authorization.

Recommendations assist operator judgment.

They do not replace operator judgment.


---

# 25. Consequence of Inaction

When reasonably known, a SITREP item should explain what happens if the
operator takes no action.

Examples include:

• Mission remains blocked,

• authorization expires,

• retry occurs automatically,

• no immediate consequence,

• storage pressure may become critical,

• evidence remains insufficient for Mission completion,

• a deadline may be missed.

JARVIS must distinguish between:

• confirmed consequence,

• likely consequence,

• possible consequence,

• unknown consequence.

The system must not present prediction as certainty.

---

# 26. Confidence

A SITREP item may include a confidence assessment when interpretation depends
upon uncertain or incomplete evidence.

Canonical confidence values are:

• Confirmed

• High

• Moderate

• Low

• Unknown

Confirmed means authoritative evidence directly supports the operational
statement.

Confidence must not be represented with unsupported numerical precision.

Unknown is preferable to fabricated certainty.

---

# 27. SITREP Item State

A SITREP item has its own presentation lifecycle.

Canonical SITREP item states are:

• Active

• Acknowledged

• Deferred

• Resolving

• Resolved

• Superseded

• Expired

These states describe the operational-attention record.

They do not replace the lifecycle state of the Mission, Objective, Task,
approval, dependency, capability, or system condition being reported.

---

# 28. Active

An Active SITREP item remains operationally relevant.

An Active item may be:

• action required,

• review recommended,

• awareness only,

• automatically resolving.

Active does not necessarily mean urgent.

Priority and state remain separate.

---

# 29. Acknowledged

Acknowledgement means the operator has seen and recognized the item.

Acknowledgement does not mean:

• approved,

• accepted,

• resolved,

• completed,

• authorized,

• dismissed,

• risk accepted.

Acknowledgement and resolution must remain separate.

An acknowledged item may remain active until its underlying condition changes.

---

# 30. Deferred

A Deferred item remains relevant but has been intentionally postponed.

Deferral should record:

• deferring actor,

• reason,

• deferral timestamp,

• review time or review condition,

• consequence of delay when known.

Deferral must not silently suppress the item forever.

Critical safety, security, integrity, or irreversible-loss conditions may
prohibit deferral.

---

# 31. Resolving

Resolving indicates that corrective or follow-up work is underway.

Examples include:

• retry executing,

• dependency restoration underway,

• approval review in progress,

• recovery Mission active,

• diagnostics running,

• verification repeated.

Resolving items remain visible until authoritative evidence confirms the
outcome.

---

# 32. Resolved

A SITREP item becomes Resolved when the underlying condition no longer requires
current operator attention.

Resolution may result from:

• authoritative state change,

• successful recovery,

• completed operator action,

• dependency restoration,

• accepted risk,

• Mission completion,

• explicit authorized decision.

Resolution must identify:

• resolving actor or service,

• resolution timestamp,

• resolution reason,

• resulting authoritative state,

• related evidence when applicable.

Resolved items may remain temporarily visible to preserve continuity.

---

# 33. Superseded

A SITREP item becomes Superseded when a newer item more accurately represents
the same operational condition.

For example:

• a warning may be superseded by a confirmed failure,

• a blocked condition may be superseded by a recovery update,

• an approval request may be superseded by an approval decision.

Superseded items should not compete visually with the current item.

They must remain traceable through correlation and history.

---

# 34. Expired

A SITREP item may expire when its period of operational relevance ends.

Expiration may occur when:

• a deadline passes,

• a Mission is archived,

• the item becomes obsolete,

• policy defines automatic expiration,

• the operational context no longer exists.

Expiration is not resolution.

An expired item may describe a condition that was never addressed.

The historical record must preserve that distinction.

---

# 35. Valid State Transitions

Examples of valid SITREP item transitions include:

Active -> Acknowledged

Active -> Deferred

Active -> Resolving

Active -> Resolved

Active -> Superseded

Active -> Expired

Acknowledged -> Deferred

Acknowledged -> Resolving

Acknowledged -> Resolved

Acknowledged -> Superseded

Acknowledged -> Expired

Deferred -> Active

Deferred -> Resolving

Deferred -> Resolved

Deferred -> Superseded

Deferred -> Expired

Resolving -> Active

Resolving -> Resolved

Resolving -> Superseded

Resolving -> Expired

Invalid transitions must be rejected or explicitly repaired.

---

# 36. State Ownership

SITREP item state is managed by the SITREP service.

The SITREP service may change presentation state based upon:

• operator acknowledgement,

• operator deferral,

• authoritative source changes,

• reconciliation,

• expiration policy,

• superseding information.

The SITREP service must not change the authoritative state of the condition it
reports unless it invokes the responsible backend service through an authorized
action.

Presentation state and operational state must remain distinct.


---

# 37. Deduplication

SITREP must prevent repeated presentation of the same operational condition.

Repeated events should update an existing SITREP item when they represent the
same underlying condition.

Deduplication may consider:

• Mission identifier,

• category,

• source condition,

• affected entity,

• correlation identifier,

• current lifecycle state,

• time window,

• recommended action.

Deduplication must not merge distinct conditions merely because they appear
similar.

---

# 38. Consolidation

Related events or conditions may be consolidated into one SITREP item when
consolidation improves clarity.

For example:

• five acquisition Tasks fail because the same source is unavailable,

• several capability checks report the same storage constraint,

• multiple Objectives wait on the same approval,

• repeated retry attempts produce the same outcome.

A consolidated item should explain:

• the shared condition,

• the affected Missions, Objectives, or Tasks,

• the common consequence,

• the recommended response.

Underlying details must remain available through progressive disclosure.

Consolidation must not hide materially different causes, risks, or actions.

---

# 39. Correlation

SITREP items should preserve correlation with the events and operational
conditions that produced them.

Correlation may connect:

• repeated failures,

• retry sequences,

• related Director reports,

• approval requests and decisions,

• dependency changes,

• recovery attempts,

• parent and child Missions.

Correlation allows JARVIS to present one coherent operational condition rather
than disconnected updates.

---

# 40. Escalation

A SITREP item may escalate when its operational consequence increases.

Escalation conditions may include:

• impact increases,

• a deadline approaches,

• retry attempts continue to fail,

• additional Missions become affected,

• uncertainty becomes confirmed risk,

• operator action remains outstanding,

• a background condition becomes Mission-blocking,

• mitigation fails.

Escalation should normally update the existing SITREP item when the underlying
condition remains the same.

Escalation must record:

• previous priority,

• new priority,

• reason,

• timestamp,

• triggering source.

---

# 41. De-escalation

A SITREP item may be de-escalated when its operational consequence decreases.

De-escalation conditions may include:

• mitigation succeeds,

• impact decreases,

• an alternative path becomes available,

• affected scope narrows,

• uncertainty is resolved favorably,

• Mission priority changes,

• required action is no longer urgent.

De-escalation must remain traceable.

It must not erase the earlier condition or imply that the earlier priority was
incorrect.

---

# 42. Recurrence

A resolved or expired condition may recur.

Recurrence should create a new operational occurrence while preserving
correlation with earlier instances.

JARVIS should distinguish between:

• continuation of the same condition,

• recurrence after resolution,

• repeated independent conditions.

Recurrence history may influence:

• priority,

• recommended action,

• confidence,

• escalation,

• recovery planning.

Repeated recurrence may indicate a systemic problem and should be surfaced
accordingly.

---

# 43. Foreground Mission Behavior

SITREP should prioritize items related to the foreground Mission.

Foreground Mission items may receive:

• higher placement,

• richer context,

• direct Mission Workspace actions,

• stronger visibility,

• more immediate explanation.

Foreground preference does not automatically increase item priority.

Priority remains based on operational consequence.

Foreground emphasis must not hide critical or high-priority background
conditions.

---

# 44. Background Mission Behavior

Background Missions may produce SITREP items without interrupting foreground
work.

Background activity should normally be:

• grouped,

• summarized,

• lower prominence,

• shown when materially relevant.

A background Mission should become more prominent when it:

• becomes blocked,

• requires approval,

• fails materially,

• affects the foreground Mission,

• threatens system integrity,

• creates security risk,

• completes an important outcome,

• requires operator judgment.

Routine background success should not produce unnecessary interruption.

---

# 45. Foreground Change

When the foreground Mission changes, SITREP presentation should adapt to the new
Operational Context.

The transition may affect:

• item ordering,

• visible Mission-specific items,

• recommended actions,

• active filters,

• contextual summaries.

Foreground change must not alter authoritative SITREP item state.

Items hidden by context remain available in the global SITREP.

---

# 46. Global SITREP

JARVIS should provide a global SITREP across authorized Missions, capabilities,
devices, and services.

The global SITREP should support filtering by:

• priority,

• category,

• Mission,

• actionability,

• unresolved state,

• assigned operator,

• time range,

• affected capability,

• affected device.

Every Mission-related item must preserve Mission identity.

The global SITREP must not become an unstructured stream.

---

# 47. Mission SITREP

Each Mission may expose a Mission-specific SITREP.

The Mission SITREP should include items related to:

• the Mission,

• its Objectives,

• its Tasks,

• its Activities,

• its dependencies,

• its approvals,

• participating Directors,

• required capabilities,

• child Missions,

• supporting Missions.

Mission-specific filtering must not hide cross-Mission conditions that
materially affect the Mission.

---

# 48. Objective and Task Context

A SITREP item may reference a specific Objective or Task.

Objective and Task context should be shown when it improves understanding or
actionability.

The operator should be able to move from a SITREP item directly to the relevant:

• Mission,

• Objective,

• Task,

• Activity,

• artifact,

• evidence,

• approval,

• capability.

Navigation must preserve Operational Context.

---

# 49. Grouping

SITREP items may be grouped by:

• Mission,

• priority,

• category,

• action required,

• shared dependency,

• shared cause,

• assigned operator,

• time period.

Grouping should reduce cognitive load.

Grouping must not obscure individual actions or critical distinctions.

Critical items should remain individually identifiable even when grouped.

---

# 50. Ordering

Default SITREP ordering should consider:

1. criticality,

2. action required,

3. foreground Mission relevance,

4. operational impact,

5. deadline,

6. recency.

Recency alone must not determine importance.

An older unresolved approval blocking the foreground Mission may be more
important than a newer informational event.

---

# 51. Summarization

JARVIS may summarize multiple low-priority or informational items.

A summary should identify:

• number of items,

• affected Missions or capabilities,

• shared category,

• overall outcome,

• whether any action is required.

Example:

    Four background maintenance activities completed successfully.
    No operator action is required.

Summaries must not hide exceptions.

If one item requires action, it should be separated from the routine summary.

---

# 52. Volume Control

SITREP must protect the operator from excessive volume.

Volume control may include:

• deduplication,

• consolidation,

• summarization,

• priority thresholds,

• expiration,

• contextual filtering,

• progressive disclosure.

Volume control must not suppress mandatory safety, security, integrity, or
authorization information.

The goal is not fewer records.

The goal is clearer operational awareness.


---

# 53. Presentation Model

SITREP presentation should remain calm, structured, and operational.

Each visible item should normally present:

1. operational condition,

2. operational significance,

3. recommended action,

4. current status.

The operator should understand the situation without opening supporting
artifacts.

Supporting evidence remains available through progressive disclosure.

---

# 54. Progressive Disclosure

SITREP should begin with concise operational summaries.

Additional information may reveal:

• source events,

• Mission context,

• Objectives,

• Tasks,

• evidence,

• Director reasoning,

• diagnostics,

• retry history,

• recovery attempts,

• related approvals,

• dependency graph.

The operator should move naturally from summary to evidence without losing
Operational Context.

---

# 55. Voice Presentation

Voice-enabled SITREP should remain concise.

Voice delivery should identify:

• affected Mission,

• operational condition,

• priority,

• whether action is required,

• recommended next action.

Voice presentation should never read implementation metadata or raw diagnostic
output unless explicitly requested.

Non-critical items should not interrupt the operator.

---

# 56. Presence Integration

JARVIS Presence may subtly reflect overall operational condition.

Presence may communicate:

• ready,

• attentive,

• processing,

• degraded,

• action required.

Presence supplements SITREP.

Presence never replaces explicit operational information.

The operator must never infer operational state solely from animation or visual
expression.

---

# 57. Operator Actions

SITREP may provide direct operational actions including:

• acknowledge,

• inspect,

• approve,

• reject,

• retry,

• assign,

• defer,

• pause Mission,

• resume Mission,

• open Mission Workspace,

• open Mission Journal,

• open supporting evidence,

• open Operations Console.

Each action must be routed through the authoritative backend service
responsible for the underlying state.

SITREP itself never modifies authoritative Mission state directly.

---

# 58. Action Safety

Every SITREP action must respect:

• operator identity,

• authorization,

• assigned role,

• Mission ownership,

• device trust,

• capability policy,

• organizational policy,

• security restrictions.

Irreversible actions should require appropriate confirmation.

The interface must clearly distinguish:

• acknowledgement,

• approval,

• execution,

• cancellation,

• deletion.

---

# 59. Startup Reconciliation

Before Commander Brief is generated, JARVIS should reconcile SITREP against
authoritative state.

Reconciliation should identify:

• unresolved approvals,

• blocked Missions,

• interrupted execution,

• completed background work,

• stale conditions,

• expired actions,

• recovered services,

• superseded SITREP items.

Known-invalid SITREP information must never be presented as current.

---

# 60. Cross-Device Continuity

Authorized operators may continue work from multiple devices.

The authoritative SITREP state should preserve:

• acknowledgement,

• deferral,

• assignment,

• resolution,

• active actions.

Presentation preferences may remain device-specific.

Operational truth must remain consistent across devices.

---

# 61. Auditability and Retention

Every significant SITREP operation should remain auditable.

Audit should record:

• creation,

• updates,

• escalation,

• de-escalation,

• acknowledgement,

• assignment,

• deferral,

• resolution,

• expiration,

• operator actions.

Resolved and expired SITREP items may leave the active operational view while
remaining available for:

• Mission Journal correlation,

• audit,

• troubleshooting,

• historical review.

SITREP should not become an unlimited notification archive.

---

# 62. Architectural Rules

The following rules are mandatory.

• SITREP is a derived operational view.

• Mission state remains authoritative.

• Every SITREP item communicates operational significance.

• Every item identifies whether action is required.

• Recommendations support operator judgment.

• Acknowledgement is not resolution.

• Related conditions should be consolidated.

• Repeated conditions should be deduplicated.

• Every item remains traceable.

• Every action routes through authoritative backend services.

• Degraded SITREP state must be disclosed.

• Operator attention must be protected.

• Commander Brief derives from SITREP and Mission state.

• Mission Journal remains the durable historical record.

• Operational Context gives every SITREP item meaning.

---

# 63. Acceptance Criteria

The SITREP architecture is complete when:

✓ SITREP is distinct from notifications, logs, events, and Mission Journal.

✓ Every item communicates operational significance.

✓ Priority and actionability are independently represented.

✓ Foreground and background Mission behavior are defined.

✓ Item lifecycle is fully specified.

✓ Deduplication and consolidation are defined.

✓ Escalation and de-escalation remain traceable.

✓ Startup reconciliation is defined.

✓ Cross-device continuity is supported.

✓ Actions route through authoritative backend services.

✓ Progressive disclosure preserves supporting evidence.

✓ The presentation protects operator attention.

---

# 64. Architectural Conclusion

SITREP is the operational intelligence layer of JARVIS Mission Control.

It does not attempt to report everything that happens.

Instead, it identifies what has become operationally meaningful.

Mission Lifecycle defines what is true.

Operational Context defines what it belongs to.

Mission Journal preserves what should be remembered.

Commander Brief restores continuity.

SITREP explains what matters now.

By separating events, state, history, and operational awareness into distinct
architectural responsibilities, JARVIS enables the operator to understand the
current situation without monitoring every subsystem directly.

The purpose of SITREP is not to attract attention.

Its purpose is to direct attention where informed judgment is required.


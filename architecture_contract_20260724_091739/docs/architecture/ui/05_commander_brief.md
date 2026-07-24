# JARVIS Commander Brief Architecture

Document ID: UI-0005

Status: Draft

Version: 1.0

Program: Mission Control Architecture

Phase: VIII-A4

---

# 1. Purpose

The Commander Brief is the primary operational briefing presented to the
operator when Mission Control begins a new session.

Its purpose is not to greet the operator.

Its purpose is to establish immediate operational awareness.

The Commander Brief answers four questions.

• What happened while I was away?

• What is happening now?

• What requires my attention?

• What should I do next?

If those questions are answered, the briefing has succeeded.

Conversation may begin afterwards.

---

# 2. Philosophy

The Commander Brief reflects the operational state of JARVIS.

It does not generate new operational truth.

Operational truth originates from authoritative backend systems including:

• Operational Context,

• Executive Director,

• Mission Engine,

• Knowledge Engine,

• Device Services,

• Verification Services,

• approved system providers.

The Commander Brief summarizes.

It never owns operational state.

---

# 3. Design Principles

Every Commander Brief shall be:

• calm,

• transparent,

• mission-oriented,

• professional,

• minimalist,

• actionable,

• trustworthy.

The Commander Brief should reduce uncertainty.

It should never increase cognitive load.

---

# 4. Commander Experience

The Commander Brief is the first operational experience after startup.

The operator should not be required to search for important information.

Critical operational information is presented immediately.

Secondary information remains available through Mission Control.

The briefing exists to orient the operator before work begins.


---

# 5. Core Operational Principle

Mission Control reduces uncertainty before it enables action.

The Commander Brief shall orient the operator before presenting commands,
recommendations, or optional detail.

The briefing must establish:

• whether JARVIS is trustworthy,

• whether the runtime is healthy,

• whether Mission context is complete,

• whether critical work failed,

• whether operator attention is required.

The briefing must never encourage action before presenting known operational
risk.

---

# 6. Attention Discipline

JARVIS shall not waste operator attention.

Every item displayed in the Commander Brief must satisfy at least one of the
following conditions.

It:

• improves situational awareness,

• restores Mission continuity,

• communicates system health,

• identifies required attention,

• requests a decision,

• recommends a useful next action.

Information that does not satisfy one of these conditions belongs elsewhere.

Routine logs do not belong in the Commander Brief.

Detailed diagnostics do not belong in the default briefing.

Low-value notifications do not belong in the Commander Brief.

---

# 7. Commander Brief Character

The Commander Brief shall feel:

• quiet,

• confident,

• prepared,

• honest,

• professional,

• deliberate.

The Commander Brief shall never feel:

• dramatic,

• hurried,

• celebratory,

• conversationally needy,

• socially manipulative,

• cluttered.

JARVIS does not attempt to maximize engagement.

JARVIS attempts to maximize operational clarity.

---

# 8. Trust Before Action

The operator must be able to determine whether the briefing is trustworthy.

The Commander Brief must identify:

• incomplete diagnostic coverage,

• stale operational data,

• unavailable state providers,

• inconsistent Mission context,

• unverified recommendations,

• degraded connectivity,

• unknown health conditions.

Uncertainty must be represented explicitly.

JARVIS must not convert unknown state into healthy state.

JARVIS must not hide degraded operation behind optimistic language.

Truth takes priority over reassurance.

---

# 9. Canonical Presentation Order

The Commander Brief follows this canonical order.

1. System Integrity

2. Mission Status

3. Changes Since Last Session

4. Attention Required

5. Recommended Next Action

6. Optional Supporting Detail

The order may be shortened when sections contain no meaningful information.

The order must not be rearranged merely for visual variety.

Critical integrity information always appears before Mission recommendations.

---

# 10. System Integrity

System Integrity establishes whether JARVIS can be trusted to continue normal
operation.

The System Integrity section may summarize:

• runtime health,

• persistent storage health,

• database availability,

• Operational Context health,

• Executive Director availability,

• Mission Engine availability,

• Knowledge Engine availability,

• local model availability,

• network state,

• device capability state,

• synchronization state.

The default presentation must remain concise.

Example:

System Integrity

Healthy

All required services available.

No critical issues detected.

Detailed diagnostics remain available on demand.


---

# 11. Mission Status

Mission Status answers one question.

"What is JARVIS currently trying to accomplish?"

Mission Status summarizes:

• active Mission,

• active Objective,

• active Task,

• current Activity,

• current execution state,

• Mission progress.

Mission Status is derived from Operational Context.

Mission Status never becomes the authoritative owner of Mission state.

Example

Mission

Mission Control Architecture

Objective

Commander Brief

Task

Architectural Specification

Status

Active

---

# 12. Mission Continuity

Mission continuity explains where work stopped.

The Commander Brief should identify:

• the previous completed Task,

• interrupted work,

• paused work,

• blocked work,

• unfinished Objectives,

• recoverable execution.

The operator should immediately understand where productive work can resume.

Mission continuity reduces the cost of returning after hours, days, or weeks.

---

# 13. Changes Since Last Session

The Commander Brief summarizes meaningful operational changes.

Examples include:

• publications acquired,

• knowledge assimilated,

• verification completed,

• software updated,

• repositories synchronized,

• new devices detected,

• completed Objectives,

• newly discovered issues.

Only meaningful operational changes should appear.

Routine background activity should remain summarized.

---

# 14. Attention Required

Attention Required identifies work that requires operator awareness.

Attention items should be prioritized.

Recommended priority order:

Critical

High

Medium

Low

Informational

Critical items always appear first.

Attention items should include:

• description,

• operational impact,

• recommended action.

Attention items should never require the operator to search for context.

---

# 15. Recommended Next Action

The Commander Brief concludes with a recommendation.

Recommendations should be derived from:

• Operational Context,

• Executive Director,

• Mission priorities,

• incomplete Objectives,

• outstanding approvals,

• current system health.

Recommendations should move the Mission forward.

Recommendations should never interrupt higher-priority operational concerns.

The recommendation should normally require one decision rather than many.


---

# 16. Commander Brief Lifecycle

The Commander Brief exists only during the startup transition into Mission
Control.

Its lifecycle is:

Fresh

↓

Presented

↓

Acknowledged

↓

Archived

Once acknowledged, Mission Workspace becomes the primary interface.

The Commander Brief may be recalled at any time from Mission Control.

---

# 17. Relationship to Operational Context

Operational Context is the authoritative source of Mission state.

Commander Brief summarizes Operational Context.

Commander Brief never owns:

• Mission,

• Objective,

• Task,

• Activity,

• Command.

If Operational Context changes, the Commander Brief reflects those changes.

Operational Context remains authoritative.

---

# 18. Relationship to SITREP

Commander Brief summarizes overall operational status.

SITREP summarizes operational events.

Commander Brief answers:

"What should I know?"

SITREP answers:

"What happened?"

The two complement one another.

Neither replaces the other.

---

# 19. Relationship to Mission Journal

Mission Journal records operational history.

Commander Brief summarizes current operational awareness.

Mission Journal answers:

"What has happened over time?"

Commander Brief answers:

"What matters right now?"

Historical information remains available through Mission Journal.

Commander Brief remains concise.

---

# 20. Multi-Device Behavior

Commander Brief shall behave consistently across every supported platform.

Examples include:

• Desktop

• Laptop

• Mobile

• Raspberry Pi

• Meta Quest

Presentation may change.

Operational meaning shall not.

Every platform presents the same operational truth.

---

# 21. Architectural Rules

The following rules are mandatory.

• Commander Brief never greets before briefing.

• Commander Brief never replaces Operational Context.

• Commander Brief always presents system integrity first.

• Commander Brief reduces uncertainty before enabling action.

• Commander Brief remains concise.

• Commander Brief recommends one clear next objective.

• Commander Brief avoids unnecessary interaction.

• Commander Brief never becomes a notification feed.

• Commander Brief never attempts to maximize engagement.

• Commander Brief exists to maximize operational awareness.

---

# 22. Acceptance Criteria

Commander Brief architecture is complete when:

✓ Operational awareness is established within seconds.

✓ System integrity is presented first.

✓ Mission continuity is restored.

✓ Attention items are prioritized.

✓ Recommendations derive from authoritative state.

✓ Operational Context remains authoritative.

✓ Commander Brief expires after acknowledgement.

✓ Mission Workspace naturally follows.

✓ Multi-device consistency is preserved.

✓ The operator understands what happened, what matters, and what to do next.

---

# 23. Architectural Conclusion

Commander Brief is the operational handoff between JARVIS and the operator.

Rather than greeting the operator, Commander Brief establishes operational
awareness.

Commander Brief restores Mission continuity.

Commander Brief summarizes trustworthy operational truth.

Commander Brief reduces uncertainty.

Commander Brief recommends the next objective.

Only after these responsibilities are fulfilled does Mission Control transition
to the Mission Workspace.

Commander Brief is therefore the canonical startup experience for JARVIS
Mission Control.


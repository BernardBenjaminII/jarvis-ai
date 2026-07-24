# JARVIS Cognitive Architecture

**Version:** 1.0  
**Status:** Canonical Architecture  
**Phase:** IX-A  
**Authority:** JARVIS Architectural Constitution  
**Related ADR:** ADR-0018 — Operational Memory as a First-Class Architectural Domain

---

# 1. Purpose

This document defines the cognitive architecture of JARVIS.

It specifies how JARVIS:

- observes,
- establishes context,
- maintains focus,
- manages working memory,
- allocates attention,
- interprets intent,
- reasons,
- plans,
- coordinates execution,
- handles interruptions,
- reflects,
- consolidates experience,
- and improves future decisions.

This document does not prescribe a particular language model, programming
language, database, framework, or user interface.

It defines enduring cognitive responsibilities and contracts.

Implementations may evolve.

The cognitive architecture must remain coherent.

---

# 2. Governing Question

The Cognitive Architecture answers:

> How does JARVIS think during a Mission?

The JARVIS Architectural Constitution defines what JARVIS is.

This document defines how its architectural domains cooperate to produce
disciplined operational cognition.

---

# 3. Cognitive Doctrine

JARVIS is not organized around prompt completion.

JARVIS is organized around sustained operational cognition.

A prompt may initiate cognition.

A conversation may communicate cognition.

A model may support cognition.

None of these individually defines cognition.

JARVIS cognition is the coordinated process through which observations become
understanding, understanding becomes decisions, decisions become action, and
action becomes experience.

---

# 4. Foundational Principles

The Cognitive Architecture inherits the constitutional principles:

> Knowledge is permanent.

> Intelligence is upgradable.

> Experience is cumulative.

> Judgment is earned.

It adds the following cognitive principles:

> Context must be explicit.

> Attention must be governed.

> Reasoning must be explainable.

> Action must be observable.

> Reflection must follow execution.

> Memory must preserve provenance.

---

# 5. Cognitive Objectives

The Cognitive Architecture exists to ensure that JARVIS can:

- maintain continuity across long-running Missions,
- distinguish current focus from background activity,
- reason from evidence rather than unsupported assumption,
- preserve uncertainty rather than conceal it,
- coordinate multiple Directors without losing Mission intent,
- recover from interruption and failure,
- explain why actions were taken,
- learn from completed operational work,
- and remain understandable to the operator.

---

# 6. Cognitive Boundaries

The Cognitive Architecture governs cognition.

It does not replace:

- the Knowledge Domain,
- the Planning Domain,
- the Execution Domain,
- Operational Memory,
- the Communication Domain,
- individual Directors,
- specialized Services,
- or operator authority.

It coordinates these responsibilities through stable cognitive contracts.

---

# 7. The Cognitive Cycle

JARVIS operates through a recurring cognitive cycle:

Observe

↓

Orient

↓

Understand

↓

Frame

↓

Reason

↓

Plan

↓

Authorize

↓

Execute

↓

Monitor

↓

Evaluate

↓

Reflect

↓

Assimilate

↓

Resume or Conclude

The cycle may repeat many times within a single Mission.

---

# 8. Observe

Observation gathers potentially relevant information.

Observation sources may include:

- operator instructions,
- Mission state,
- environmental state,
- Director reports,
- service results,
- system events,
- diagnostics,
- sensor input,
- external data,
- retrieved knowledge,
- Operational Memory,
- deadlines,
- constraints,
- and policy state.

Observation records what is available.

Observation does not determine meaning by itself.

---

# 9. Orient

Orientation establishes the relationship between observations and the current
operational situation.

Orientation determines:

- which Mission is active,
- which objective is in focus,
- which task is currently actionable,
- what changed,
- which constraints apply,
- which authorities are available,
- and what risks require attention.

Orientation prevents isolated observations from being interpreted without
context.

---

# 10. Understand

Understanding transforms observations into an explicit situational model.

Understanding may identify:

- entities,
- relationships,
- temporal order,
- dependencies,
- intent,
- ambiguity,
- conflict,
- missing information,
- operational significance,
- and potential consequences.

Understanding answers:

> What appears to be happening?

Understanding remains provisional when evidence is incomplete.

---

# 11. Frame

Framing defines the immediate cognitive problem.

A frame should specify:

- the current Mission,
- the active objective,
- the relevant task,
- the decision or action required,
- the evidence currently available,
- applicable constraints,
- known uncertainty,
- and the success condition.

Framing prevents cognitive effort from drifting toward unrelated but
interesting activity.

---

# 12. Reason

Reasoning evaluates the active frame.

Reasoning may:

- generate hypotheses,
- compare alternatives,
- identify contradictions,
- estimate confidence,
- assess risk,
- discover dependencies,
- retrieve relevant experience,
- and recommend a course of action.

Reasoning consumes evidence.

Reasoning does not silently manufacture certainty.

---

# 13. Plan

Planning converts a selected conclusion into coordinated future action.

Planning should define:

- objectives,
- tasks,
- ordering,
- dependencies,
- resources,
- Directors,
- capabilities,
- checkpoints,
- contingencies,
- authorization requirements,
- and success criteria.

Planning owns future intent.

Planning does not claim that planned work has occurred.

---

# 14. Authorize

Authorization determines whether execution may proceed.

Authorization may be granted by:

- the operator,
- standing policy,
- delegated authority,
- a Mission-specific rule,
- or a constrained autonomous operating mode.

High-impact or irreversible actions should require stronger authorization than
low-risk reversible actions.

Authorization must remain auditable.

---

# 15. Execute

Execution performs authorized work.

Execution coordinates:

- Directors,
- Services,
- capabilities,
- tools,
- workflows,
- and external systems.

Execution must emit observable events.

A significant action that leaves no trace is architecturally incomplete.

---

# 16. Monitor

Monitoring observes execution while it occurs.

Monitoring should detect:

- progress,
- completion,
- deviation,
- delay,
- failure,
- resource exhaustion,
- policy violation,
- unexpected side effects,
- and newly relevant information.

Monitoring allows cognition to adapt before failure becomes irreversible.

---

# 17. Evaluate

Evaluation compares actual results against expected results.

Evaluation considers:

- success criteria,
- quality thresholds,
- evidence returned,
- confidence,
- operational cost,
- unintended effects,
- and remaining uncertainty.

Evaluation determines whether JARVIS should:

- continue,
- retry,
- replan,
- escalate,
- pause,
- or conclude.

---

# 18. Reflect

Reflection examines completed or interrupted cognitive activity.

Reflection asks:

- What happened?
- What was expected?
- What differed?
- Why did it differ?
- Which assumptions were valid?
- Which assumptions failed?
- What should be preserved?
- What should change?

Reflection produces lesson candidates.

It does not automatically declare every observation a permanent lesson.

---

# 19. Assimilate

Assimilation integrates validated experience into Operational Memory.

Assimilation preserves:

- originating Mission,
- evidence,
- confidence,
- applicability,
- contradictions,
- review state,
- and historical context.

Assimilation must never rewrite the original Mission record.

---

# 20. Resume or Conclude

After evaluation and reflection, JARVIS must explicitly determine whether to:

- resume the current task,
- continue to the next task,
- replan the objective,
- suspend the Mission,
- await operator input,
- transfer responsibility,
- or conclude the Mission.

Cognitive activity should not continue merely because processing remains
possible.

---

# 21. Cognitive State

Cognitive State is the explicit representation of what JARVIS is currently
thinking about operationally.

Canonical Cognitive State includes:

- active Mission identifier,
- active objective identifier,
- active task identifier,
- current frame,
- current focus,
- active hypotheses,
- selected plan,
- pending decisions,
- uncertainty,
- authorization state,
- interruption state,
- and resume point.

Cognitive State must be inspectable.

---

# 22. Working Memory

Working Memory contains information required for immediate cognitive activity.

Working Memory may contain:

- current instructions,
- current frame,
- active evidence,
- temporary conclusions,
- recent events,
- pending tool results,
- short-lived calculations,
- active hypotheses,
- and immediate constraints.

Working Memory is limited.

Working Memory is not permanent storage.

---

# 23. Working Memory Admission

Information enters Working Memory only when it is relevant to current or
anticipated cognitive activity.

Admission should consider:

- Mission relevance,
- objective relevance,
- urgency,
- dependency,
- evidentiary value,
- operator priority,
- and cognitive cost.

Admission must not be based solely on recency.

---

# 24. Working Memory Eviction

Working Memory requires deliberate eviction.

Information may be evicted when it is:

- no longer relevant,
- superseded,
- safely persisted elsewhere,
- duplicated,
- resolved,
- or outside current cognitive scope.

Eviction must not destroy information that has not been durably recorded when
durable recording is required.

---

# 25. Working Memory Compression

Large cognitive contexts should be compressed into structured summaries.

Compression should preserve:

- intent,
- decisions,
- unresolved questions,
- evidence references,
- confidence,
- constraints,
- and resume information.

Compression must not silently convert uncertainty into certainty.

---

# 26. Context

Context is the structured environment in which cognition occurs.

Context may include:

- operator identity,
- Mission identity,
- operational role,
- current objective,
- location,
- time,
- system state,
- device capability,
- permissions,
- policies,
- active evidence,
- and relevant history.

Context should be explicit rather than implied.

---

# 27. Context Assembly

Context Assembly gathers information needed for a cognitive operation.

Context Assembly should retrieve the minimum sufficient context rather than
every potentially related record.

Context Assembly may combine:

- Working Memory,
- Mission state,
- Knowledge retrieval,
- Operational Memory retrieval,
- Director state,
- policy,
- and environmental observations.

---

# 28. Context Provenance

Every material item placed into cognitive context should retain its source.

Context provenance may identify:

- operator instruction,
- knowledge record,
- Mission event,
- Director report,
- service output,
- inference,
- or historical experience.

A conclusion should be distinguishable from a source observation.

---

# 29. Context Freshness

Context should communicate freshness.

Information may be:

- current,
- recently observed,
- historically valid,
- stale,
- superseded,
- or unknown.

Time-sensitive information must not be presented as current merely because it
exists in memory.

---

# 30. Context Conflict

Conflicting context must remain visible until resolved.

Conflict resolution may involve:

- source comparison,
- confidence comparison,
- temporal analysis,
- operator clarification,
- additional acquisition,
- or explicit uncertainty.

JARVIS must not silently select the most convenient version of reality.

---

# 31. Attention

Attention determines which information receives immediate cognitive resources.

Attention is a governed allocation mechanism.

Attention is not merely similarity scoring.

Attention should consider:

- Mission importance,
- urgency,
- risk,
- dependency,
- novelty,
- uncertainty,
- operator direction,
- and potential consequence.

---

# 32. Focus

Focus identifies the primary subject of immediate cognitive effort.

Only one item should normally occupy primary focus.

Supporting items may remain in secondary focus.

Background activities may continue without competing for primary focus unless
they produce a qualifying interruption.

---

# 33. Focus Stack

JARVIS should maintain a Focus Stack.

A Focus Stack entry should preserve:

- Mission,
- objective,
- task,
- reason for focus,
- entry timestamp,
- suspension reason,
- resume condition,
- and prior context reference.

The Focus Stack allows interrupted cognition to resume coherently.

---

# 34. Mission Focus

Mission Focus represents the Mission currently receiving primary cognitive
attention.

JARVIS may supervise multiple Missions.

Only one Mission should ordinarily control the primary interaction context at a
time.

Mission Focus must remain visible to the operator.

---

# 35. Objective Focus

Objective Focus identifies the active objective within the focused Mission.

Objective Focus helps prevent task-level activity from becoming detached from
Mission intent.

Every task should be traceable to an objective.

Every objective should be traceable to Mission intent.

---

# 36. Attention Budget

Cognitive activity consumes finite resources.

JARVIS should maintain an Attention Budget that considers:

- computation,
- time,
- memory,
- tool availability,
- energy,
- network access,
- model availability,
- and operator tolerance.

High-cost cognition should be justified by operational value.

---

# 37. Cognitive Load

Cognitive Load represents the burden imposed by active context, unresolved
decisions, concurrent operations, and information volume.

Excessive cognitive load may cause:

- missed dependencies,
- context loss,
- poor prioritization,
- unstable reasoning,
- and operator confusion.

When cognitive load becomes excessive, JARVIS should compress, defer, delegate,
or request prioritization.

---

# 38. Prioritization

Prioritization orders competing cognitive demands.

Priority should consider:

- operator instruction,
- Mission criticality,
- urgency,
- safety,
- reversibility,
- dependency,
- expected value,
- and cost of delay.

Priority must be explainable.

---

# 39. Interruptions

An interruption is an event that competes with current focus.

Interruptions may originate from:

- the operator,
- a Director,
- a safety condition,
- a policy condition,
- a deadline,
- a system failure,
- a security alert,
- or a material change in evidence.

Not every event deserves interruption.

---

# 40. Interruption Classification

Interruptions should be classified.

Canonical classes include:

- informational,
- advisory,
- important,
- urgent,
- critical,
- and emergency.

Classification determines whether the interruption:

- enters the activity feed,
- appears as an alert,
- requests acknowledgment,
- suspends current work,
- or immediately overrides current focus.

---

# 41. Interruption Handling

When an interruption changes focus, JARVIS should preserve:

- current frame,
- Working Memory summary,
- pending actions,
- authorization state,
- unresolved questions,
- and resume condition.

Interruption handling must not destroy the cognitive path that preceded it.

---

# 42. Resume Semantics

Resuming an interrupted activity requires reorientation.

JARVIS should verify:

- whether the Mission remains active,
- whether assumptions remain valid,
- whether evidence has changed,
- whether deadlines changed,
- whether authorization remains valid,
- and whether the original plan is still appropriate.

Resume is not equivalent to blindly continuing.

---

# 43. Goal Structure

Goals exist within a canonical hierarchy:

Mission Intent

↓

Objectives

↓

Tasks

↓

Activities

↓

Commands

Higher levels define purpose.

Lower levels define realization.

No lower-level action should become detached from higher-level intent.

---

# 44. Goal Stack

The Goal Stack maintains active and pending goals.

Each goal should include:

- identifier,
- parent,
- owner,
- priority,
- state,
- dependencies,
- success criteria,
- failure criteria,
- and completion evidence.

The Goal Stack provides continuity across cognitive cycles.

---

# 45. Goal Conflict

Goals may conflict.

Conflict may involve:

- resources,
- timing,
- policy,
- safety,
- operator preference,
- or mutually exclusive outcomes.

Conflicting goals must be surfaced and resolved.

JARVIS must not conceal goal conflict through arbitrary execution order.

---

# 46. Goal Abandonment

A goal may be abandoned when:

- it is no longer relevant,
- its parent objective is cancelled,
- its cost exceeds its expected value,
- required authorization is denied,
- dependencies become impossible,
- or the operator directs abandonment.

Abandonment must include a recorded reason.

---

# 47. Hypotheses

A hypothesis is a provisional explanation or prediction.

Hypotheses should include:

- statement,
- supporting evidence,
- contradicting evidence,
- confidence,
- assumptions,
- validation method,
- and state.

Hypotheses are not facts.

---

# 48. Hypothesis Lifecycle

Canonical hypothesis states include:

- proposed,
- supported,
- challenged,
- testing,
- validated,
- rejected,
- superseded,
- and unresolved.

State transitions should be evidence-driven.

---

# 49. Confidence

Confidence represents the strength of support for a conclusion.

Confidence should reflect:

- source quality,
- evidence quantity,
- evidence independence,
- contradiction,
- uncertainty,
- temporal relevance,
- and historical reliability.

Confidence is not certainty.

---

# 50. Confidence Propagation

Derived conclusions should not possess greater confidence than their supporting
evidence permits.

Confidence propagation must consider:

- weak dependencies,
- uncertain assumptions,
- contradictory evidence,
- and chained inference.

Long reasoning chains should expose accumulated uncertainty.

---

# 51. Self-Verification

Before presenting or executing a significant conclusion, JARVIS should perform
self-verification appropriate to the risk.

Self-verification may include:

- evidence reinspection,
- contradiction search,
- independent reasoning path,
- rule validation,
- simulation,
- test execution,
- or operator review.

Verification effort should scale with consequence.

---

# 52. Alternative Generation

Material decisions should consider alternatives.

Alternatives should include:

- expected benefit,
- cost,
- risk,
- reversibility,
- dependencies,
- confidence,
- and operational consequences.

The selected alternative should remain explainable.

---

# 53. Decision Record

Significant decisions should generate a Decision Record.

A Decision Record should preserve:

- decision,
- authority,
- context,
- alternatives,
- evidence,
- reasoning,
- confidence,
- timestamp,
- expected outcome,
- and review condition.

Decision Records support later reflection.

---

# 54. Director Coordination

Directors coordinate operational responsibilities within architectural domains.

The Cognitive Architecture governs how Director contributions are combined.

Directors should communicate through:

- explicit requests,
- explicit responses,
- structured events,
- confidence,
- status,
- and failure reports.

Hidden Director state should not become a dependency of another Director.

---

# 55. Executive Director

The Executive Director coordinates the overall cognitive cycle.

Responsibilities include:

- interpreting operator intent,
- establishing Mission Focus,
- selecting participating Directors,
- maintaining cognitive continuity,
- enforcing policy,
- coordinating Planning and Execution,
- monitoring progress,
- escalating decisions,
- and ensuring reflection occurs.

The Executive Director coordinates cognition.

It does not perform every specialized function directly.

---

# 56. Director Delegation

Delegation should define:

- requested outcome,
- Mission context,
- constraints,
- authority,
- expected response,
- deadline,
- and failure behavior.

Delegation without explicit boundaries creates architectural ambiguity.

---

# 57. Director Reports

Director reports should include:

- status,
- result,
- evidence,
- confidence,
- limitations,
- exceptions,
- next recommended action,
- and relevant events.

Reports should distinguish observation from interpretation.

---

# 58. Director Conflict

Directors may produce conflicting recommendations.

Conflict resolution should consider:

- domain authority,
- evidence quality,
- policy,
- Mission priority,
- uncertainty,
- and operator authority.

The Executive Director should not hide material disagreement.

---

# 59. Capability Selection

Capability selection should be based on fitness for the active cognitive frame.

Selection may consider:

- capability contract,
- historical performance,
- platform availability,
- cost,
- risk,
- latency,
- confidence,
- and policy.

The most powerful capability is not always the most appropriate capability.

---

# 60. Model Independence

No model is the mind of JARVIS.

Models are cognitive resources.

A model may support:

- interpretation,
- reasoning,
- planning,
- summarization,
- generation,
- classification,
- or verification.

Models must remain replaceable.

Cognitive continuity must survive model replacement.

---

# 61. Multi-Model Cognition

JARVIS may use multiple models within one cognitive cycle.

Different models may specialize in:

- coding,
- planning,
- extraction,
- vision,
- speech,
- verification,
- or low-latency interaction.

Model selection should be governed by capability contracts and operational
requirements.

---

# 62. Tool Use

Tools extend cognition into external action.

Tool use requires:

- a defined objective,
- appropriate authorization,
- validated inputs,
- observable execution,
- result inspection,
- and failure handling.

Tool output must not be accepted without interpretation or verification when
risk warrants verification.

---

# 63. Cognitive Safety

Cognitive Safety prevents reasoning and action from exceeding authority or
acceptable risk.

Safety controls may include:

- authorization boundaries,
- capability restrictions,
- sandboxing,
- rate limits,
- data classification,
- action previews,
- confirmation,
- and emergency stop.

Safety is an architectural responsibility.

It is not an interface decoration.

---

# 64. Reversibility

JARVIS should prefer reversible actions when uncertainty is material.

A plan should identify:

- reversible steps,
- irreversible steps,
- rollback procedures,
- restore points,
- and decision gates.

Irreversible actions require stronger confidence and authorization.

---

# 65. Failure Handling

Failure is a normal cognitive condition.

Failure handling should distinguish:

- capability failure,
- service failure,
- evidence failure,
- plan failure,
- authorization failure,
- environmental failure,
- and reasoning failure.

Different failure classes require different recovery strategies.

---

# 66. Retry

Retry is appropriate only when the cause of failure permits a meaningful chance
of success.

Retry policy should consider:

- failure classification,
- attempt count,
- backoff,
- changed conditions,
- cost,
- and idempotency.

Blind repetition is not recovery.

---

# 67. Replanning

Replanning is required when:

- assumptions change,
- dependencies fail,
- evidence changes,
- priorities change,
- resources disappear,
- or success criteria become unreachable.

Replanning should preserve the original plan and explain why it was replaced.

---

# 68. Escalation

Escalation transfers a decision to a higher authority or more capable
subsystem.

Escalation may be required by:

- uncertainty,
- risk,
- policy,
- insufficient authority,
- repeated failure,
- or conflicting goals.

Escalation is a disciplined cognitive action.

It is not failure avoidance.

---

# 69. Cognitive Events

Meaningful changes in Cognitive State should emit events.

Examples include:

- focus changed,
- frame established,
- hypothesis proposed,
- decision requested,
- authorization granted,
- execution started,
- execution failed,
- replan initiated,
- reflection completed,
- and Mission concluded.

Events enable observability without exposing private implementation details.

---

# 70. Cognitive Observability

Operators should be able to understand:

- what JARVIS is focused on,
- why it is focused there,
- what it currently believes,
- how confident it is,
- what it plans to do,
- what it is doing,
- what is blocked,
- and what requires operator attention.

Observability should not require exposing hidden chain-of-thought.

Structured rationale, evidence, decisions, and state are sufficient.

---

# 71. Cognitive Explanation

Explanation should communicate:

- relevant facts,
- evidence,
- assumptions,
- alternatives,
- uncertainty,
- selected action,
- and expected consequences.

Explanation should be appropriate to the operator's requested depth.

Explanation is not the verbatim reproduction of internal model reasoning.

---

# 72. Commander Brief Integration

The Commander Brief presents high-level cognitive orientation.

It may communicate:

- current Mission Focus,
- active objectives,
- recent outcomes,
- unresolved blockers,
- important changes,
- pending decisions,
- and recommended next action.

The Commander Brief consumes Cognitive State.

It does not own Cognitive State.

---

# 73. Mission Workspace Integration

The Mission Workspace presents the active Mission context.

It may display:

- intent,
- objectives,
- tasks,
- current focus,
- plan,
- evidence,
- progress,
- Director activity,
- and operational outputs.

The Mission Workspace renders authoritative backend state.

It must not invent independent Mission truth.

---

# 74. SITREP Integration

The SITREP communicates current operational condition.

It should summarize:

- Mission state,
- progress,
- changes,
- blockers,
- risk,
- Director activity,
- and recommended operator attention.

SITREP is a communication product.

It is not the underlying cognitive state itself.

---

# 75. Operational Memory Integration

Cognition retrieves experience from Operational Memory when past Missions may
inform current judgment.

Retrieved experience should include:

- applicability,
- provenance,
- confidence,
- differences from the current Mission,
- and historical outcome.

Historical similarity must not be treated as proof of identical conditions.

---

# 76. Knowledge Integration

Cognition retrieves verified knowledge from the Knowledge Domain.

Knowledge retrieval should preserve:

- source,
- provenance,
- confidence,
- version,
- date,
- and contradiction state.

Reasoning should distinguish verified knowledge from unverified observation.

---

# 77. Procedural Memory

Procedural Memory preserves validated methods for performing recurring work.

Procedures may include:

- workflows,
- checklists,
- runbooks,
- capability sequences,
- recovery procedures,
- and verification routines.

Procedural Memory answers:

> How should this kind of work be performed?

---

# 78. Cognitive Consolidation

Cognitive Consolidation determines what should persist after immediate work
ends.

Possible destinations include:

- Mission Journal,
- Decision Record,
- After Action Review,
- Operational Memory,
- Procedural Memory,
- Knowledge review queue,
- or deliberate discard.

Not every temporary thought deserves permanent retention.

---

# 79. Deliberate Forgetting

JARVIS requires deliberate forgetting.

Temporary, duplicated, low-value, or invalid cognitive material should not
accumulate indefinitely.

Forgetting should preserve any required audit or historical record while
removing unnecessary active burden.

Forgetting is resource governance.

It is not historical revision.

---

# 80. Long-Running Cognition

Long-running Missions require durable cognitive continuity.

JARVIS should persist:

- Mission Focus,
- Goal Stack,
- Focus Stack,
- pending decisions,
- active plans,
- checkpoints,
- resume conditions,
- and relevant context references.

A restart should not erase Mission understanding.

---

# 81. Cross-Device Cognition

Cognitive continuity should survive movement between devices.

Cross-device transfer must preserve:

- Mission identity,
- Cognitive State,
- authority,
- context references,
- pending decisions,
- and resume point.

Device-specific capabilities may differ.

Mission intent must remain stable.

---

# 82. Distributed Cognition

JARVIS may coordinate cognition across multiple runtimes.

Distributed cognition requires:

- stable identities,
- explicit authority,
- state ownership,
- synchronization,
- conflict handling,
- and event ordering.

Distribution must not create multiple competing authoritative minds for the same
Mission.

---

# 83. Offline Cognition

JARVIS should retain useful cognitive capability without network access.

Offline operation may rely on:

- local models,
- local knowledge,
- cached operational context,
- local procedures,
- and deferred synchronization.

Offline limitations must remain visible.

---

# 84. Cognitive Degradation

When preferred resources are unavailable, JARVIS should degrade explicitly.

Degradation modes may include:

- reduced model capability,
- reduced context,
- local-only knowledge,
- delayed execution,
- restricted tools,
- or operator-dependent planning.

Degraded operation must not masquerade as full capability.

---

# 85. Cognitive Performance

Cognitive performance should be assessed by more than response speed.

Measures may include:

- decision quality,
- evidence quality,
- Mission success,
- plan stability,
- recovery effectiveness,
- operator burden,
- explanation quality,
- resource efficiency,
- and lesson reuse.

Fast but unreliable cognition is not superior cognition.

---

# 86. Cognitive Quality

Cognitive quality should consider:

- correctness,
- relevance,
- completeness,
- traceability,
- uncertainty handling,
- consistency,
- safety,
- and operational usefulness.

Quality should be measured across complete cognitive cycles.

---

# 87. Cognitive Evaluation

Cognitive architecture should support deterministic and scenario-based
evaluation.

Evaluation may test:

- focus preservation,
- interruption recovery,
- context integrity,
- confidence propagation,
- Director coordination,
- replanning,
- authorization,
- and consolidation.

Evaluation should include failure and degraded-mode scenarios.

---

# 88. Cognitive Invariants

The following invariants should remain true:

1. Every cognitive operation belongs to a Mission or explicit non-Mission
   interaction.

2. Every active task traces to an objective.

3. Every objective traces to Mission intent.

4. Every significant decision preserves evidence and authority.

5. Every significant action emits an observable event.

6. Every interruption preserves a resume path.

7. Every material conclusion communicates uncertainty.

8. Every permanent lesson preserves provenance.

9. No model owns permanent knowledge.

10. No interface owns authoritative cognitive state.

---

# 89. Prohibited Patterns

The following patterns violate the Cognitive Architecture:

- treating conversation history as the only memory,
- treating a model context window as authoritative state,
- allowing UI state to become Mission truth,
- silently discarding uncertainty,
- hiding material Director disagreement,
- retrying without failure classification,
- executing irreversible action without appropriate authorization,
- storing unsupported inference as verified knowledge,
- rewriting historical Mission records,
- and coupling cognition permanently to one model provider.

---

# 90. Acceptance Criteria

Phase IX-A Cognitive Architecture is complete when:

- the cognitive cycle is defined,
- Cognitive State is defined,
- Working Memory responsibilities are defined,
- context assembly and provenance are defined,
- attention and focus are governed,
- interruptions and resume semantics are defined,
- goal and hypothesis structures are defined,
- confidence and self-verification are defined,
- Director coordination is defined,
- model independence is preserved,
- safety and failure recovery are defined,
- UI integrations remain presentation-only,
- memory consolidation is defined,
- long-running and cross-device cognition are addressed,
- invariants are explicit,
- and implementation remains technology independent.

---

# 91. Implementation Sequence

Implementation should proceed in controlled stages.

Recommended sequence:

1. Cognitive contracts and state models.

2. Working Memory repository.

3. Focus Stack and Goal Stack.

4. Context Assembly Service.

5. Attention and prioritization policy.

6. Interruption and resume handling.

7. Executive Director cognitive coordinator.

8. Director request and report contracts.

9. Decision Records.

10. Cognitive event stream.

11. Cognitive observability API.

12. Commander Brief and Mission Workspace integration.

13. Operational Memory consolidation.

14. Cross-device continuity.

15. Scenario-based cognitive verification.

No implementation stage should bypass the invariants defined in this document.

---

# 92. Relationship to Future Phases

Phase IX-A defines cognition.

Phase IX-B will define the Reasoning Engine.

Phase IX-C will define the Planning Engine.

Phase IX-D will refine Executive Director implementation.

Phase IX-E will implement memory consolidation.

Phase IX-F will implement operational learning.

Phase X will redesign Mission Control UI around these stable cognitive
contracts.

The UI redesign is therefore deferred, not abandoned.

Its architecture will be stronger because the backend cognitive model will
already be explicit.

---

# 93. Guiding Doctrine

JARVIS should always know:

- what Mission it is serving,
- what objective it is advancing,
- what task it is performing,
- what evidence it is using,
- what assumptions it is making,
- how confident it is,
- what authority it possesses,
- what action it intends,
- what happened,
- and what should be learned.

A system that cannot answer these questions does not possess disciplined
operational cognition.

---

# 94. Conclusion

Cognition is not a model response.

Cognition is an accountable operational process.

JARVIS observes deliberately.

JARVIS focuses explicitly.

JARVIS reasons from evidence.

JARVIS plans toward Mission intent.

JARVIS acts within authority.

JARVIS monitors outcomes.

JARVIS reflects on experience.

JARVIS preserves what should be remembered.

JARVIS improves through disciplined repetition.

Knowledge is permanent.

Intelligence is upgradable.

Experience is cumulative.

Judgment is earned.


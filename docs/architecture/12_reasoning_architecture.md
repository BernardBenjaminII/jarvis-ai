# JARVIS Explainable Reasoning Architecture

**Version:** 1.0  
**Status:** Canonical Architecture  
**Phase:** IX-B  
**Authority:** JARVIS Architectural Constitution  
**Parent Architecture:** `docs/architecture/11_cognitive_architecture.md`

---

# 1. Purpose

This document defines the Explainable Reasoning Architecture of JARVIS.

It establishes how JARVIS:

- represents evidence,
- distinguishes observations from conclusions,
- constructs claims,
- generates hypotheses,
- identifies alternatives,
- detects contradictions,
- assesses confidence,
- evaluates risk,
- records assumptions,
- selects recommendations,
- verifies conclusions,
- and communicates structured explanations.

This architecture governs reasoning behavior.

It does not prescribe:

- a specific language model,
- a specific prompt,
- a specific vector database,
- a specific inference framework,
- a specific programming language,
- or a specific user interface.

Implementations may evolve.

Reasoning accountability must remain stable.

---

# 2. Governing Question

The Reasoning Architecture answers:

> How does JARVIS reach a defensible conclusion?

A defensible conclusion should preserve:

- the question being answered,
- the evidence considered,
- the assumptions made,
- the alternatives evaluated,
- the uncertainties present,
- the risks identified,
- the authority involved,
- and the reason the conclusion was selected.

---

# 3. Reasoning Doctrine

JARVIS does not treat fluent language as proof of correct reasoning.

A persuasive response may still be unsupported.

A concise response may still be well reasoned.

Reasoning quality is determined by the relationship between:

- evidence,
- inference,
- alternatives,
- uncertainty,
- decisions,
- and outcomes.

The purpose of reasoning is not to sound intelligent.

The purpose of reasoning is to produce reliable operational judgment.

---

# 4. Architectural Relationship

The Cognitive Architecture governs the complete cognitive cycle.

The Reasoning Architecture governs the reasoning stage within that cycle.

Canonical relationship:

Observe

↓

Orient

↓

Understand

↓

Frame

↓

**Reason**

↓

Plan

↓

Authorize

↓

Execute

↓

Evaluate

↓

Reflect

The Reasoning Architecture consumes a Cognitive Frame.

It produces structured Reasoning Results.

It does not own Mission state.

It does not execute actions.

It does not own permanent knowledge.

---

# 5. Reasoning Principles

JARVIS reasoning shall follow these principles:

1. Evidence precedes conclusion.

2. Observation remains distinguishable from inference.

3. Assumptions remain explicit.

4. Uncertainty remains visible.

5. Contradictions remain unresolved until evaluated.

6. Significant decisions consider alternatives.

7. Confidence reflects evidence quality.

8. Risk influences verification depth.

9. Conclusions remain traceable.

10. Models remain replaceable.

---

# 6. Reasoning Inputs

Reasoning may consume:

- Cognitive State,
- the active Cognitive Frame,
- operator instructions,
- Mission objectives,
- verified knowledge,
- Operational Memory,
- Director reports,
- service outputs,
- execution observations,
- policies,
- constraints,
- deadlines,
- capability state,
- environmental state,
- and unresolved questions.

Every material input should retain provenance.

---

# 7. Reasoning Outputs

Reasoning may produce:

- clarified questions,
- claims,
- hypotheses,
- alternatives,
- contradiction reports,
- uncertainty reports,
- risk assessments,
- recommendations,
- decisions,
- verification requests,
- escalation requests,
- and structured explanations.

Reasoning outputs are not actions.

Execution remains the responsibility of the Execution Domain.

---

# 8. Reasoning Case

A Reasoning Case is the authoritative container for one bounded reasoning
operation.

A Reasoning Case should include:

- case identifier,
- Mission identifier,
- objective identifier,
- task identifier,
- initiating question,
- Cognitive Frame reference,
- status,
- priority,
- authority,
- created timestamp,
- updated timestamp,
- participating Directors,
- evidence references,
- claims,
- hypotheses,
- alternatives,
- assumptions,
- contradictions,
- confidence,
- risks,
- decision,
- explanation,
- and verification state.

---

# 9. Reasoning Case Lifecycle

Canonical Reasoning Case states include:

- created,
- framing,
- collecting_evidence,
- generating_hypotheses,
- evaluating,
- awaiting_information,
- awaiting_authorization,
- verifying,
- decided,
- inconclusive,
- escalated,
- superseded,
- and closed.

State transitions must be explicit.

A case should not silently move from uncertainty to decision.

---

# 10. Reasoning Scope

Each Reasoning Case must have a bounded scope.

Scope should identify:

- the question,
- the decision boundary,
- the relevant Mission context,
- excluded concerns,
- time horizon,
- acceptable confidence,
- and required authority.

Unbounded reasoning creates uncontrolled cognitive load.

---

# 11. Question Formulation

A reasoning operation begins with an explicit question.

Questions may be:

- factual,
- diagnostic,
- comparative,
- predictive,
- causal,
- strategic,
- evaluative,
- procedural,
- or decisional.

The question type influences:

- evidence requirements,
- alternative generation,
- confidence evaluation,
- and verification method.

---

# 12. Question Decomposition

Complex questions may be decomposed into subquestions.

Each subquestion should remain traceable to the parent question.

Decomposition should identify:

- dependencies,
- required evidence,
- parallelizable work,
- unresolved ambiguity,
- and completion conditions.

Subquestion answers should not be combined without preserving their individual
confidence and assumptions.

---

# 13. Clarification

JARVIS should clarify a question when ambiguity materially affects the result.

Clarification may involve:

- operator inquiry,
- context retrieval,
- policy lookup,
- assumption declaration,
- or multiple conditional conclusions.

Minor ambiguity may be handled through explicit assumptions.

Material ambiguity should not be concealed.

---

# 14. Evidence

Evidence is information used to support or challenge a claim.

Evidence may originate from:

- verified knowledge,
- direct observation,
- authoritative records,
- operator testimony,
- system telemetry,
- Director reports,
- tool results,
- experiments,
- tests,
- simulations,
- or prior operational experience.

Evidence must retain provenance.

---

# 15. Evidence Record

An Evidence Record should include:

- evidence identifier,
- source type,
- source reference,
- content reference,
- observation timestamp,
- acquisition timestamp,
- freshness,
- authority,
- reliability,
- relevance,
- independence,
- confidence,
- verification state,
- and contradiction state.

Evidence should be referenced rather than duplicated when possible.

---

# 16. Evidence Classification

Evidence may be classified as:

- direct,
- indirect,
- corroborating,
- contradicting,
- contextual,
- historical,
- experimental,
- testimonial,
- inferred,
- or missing.

Classification affects evidentiary weight.

Inferred material must not be represented as direct evidence.

---

# 17. Evidence Quality

Evidence Quality should consider:

- source authority,
- source reliability,
- directness,
- freshness,
- completeness,
- reproducibility,
- internal consistency,
- external corroboration,
- independence,
- and relevance.

A large quantity of weak evidence does not automatically outweigh a smaller
quantity of strong evidence.

---

# 18. Evidence Freshness

Reasoning must account for time.

Evidence may be:

- current,
- recent,
- historical,
- stale,
- superseded,
- or temporally unknown.

Time-sensitive conclusions should not rely on stale evidence without explicit
qualification.

---

# 19. Evidence Independence

Multiple records derived from one original source are not independent evidence.

Reasoning should detect shared provenance where possible.

Repeated publication does not necessarily increase evidentiary strength.

Independence should influence confidence calculations.

---

# 20. Evidence Admission

Evidence enters a Reasoning Case when it is materially relevant.

Admission should consider:

- question relevance,
- source quality,
- temporal relevance,
- expected information value,
- duplication,
- cost,
- and risk.

Evidence Admission should remain auditable.

---

# 21. Evidence Exclusion

Evidence may be excluded when it is:

- irrelevant,
- duplicated,
- corrupted,
- unverifiable,
- superseded,
- outside the case scope,
- prohibited by policy,
- or unreliable beyond acceptable limits.

Exclusion should preserve a reason.

Excluded evidence should not silently disappear from the audit record when it
materially influenced earlier reasoning.

---

# 22. Evidence Gap

An Evidence Gap exists when a conclusion requires information that is absent or
insufficient.

An Evidence Gap should identify:

- missing information,
- why it matters,
- expected value,
- possible acquisition methods,
- cost,
- deadline,
- and consequence of proceeding without it.

Evidence Gaps may result in:

- acquisition,
- assumption,
- conditional reasoning,
- escalation,
- or an inconclusive result.

---

# 23. Observation

An Observation records what was perceived or reported.

Observation does not automatically establish:

- cause,
- intent,
- meaning,
- reliability,
- or consequence.

Observations should remain distinguishable from interpretations.

---

# 24. Claim

A Claim is a proposition asserted within a Reasoning Case.

A Claim should include:

- claim identifier,
- statement,
- claim type,
- supporting evidence,
- contradicting evidence,
- assumptions,
- confidence,
- status,
- and provenance.

Claims may be factual, causal, predictive, normative, or procedural.

---

# 25. Claim Status

Canonical Claim states include:

- proposed,
- supported,
- challenged,
- disputed,
- verified,
- rejected,
- superseded,
- conditional,
- and unresolved.

Claim state transitions should be evidence-driven.

---

# 26. Claim Graph

Claims may form a graph.

A Claim Graph may represent:

- support,
- contradiction,
- dependency,
- implication,
- qualification,
- exception,
- and supersession.

The graph should allow JARVIS to identify which conclusions depend on weak or
disputed claims.

---

# 27. Assumption

An Assumption is a proposition temporarily accepted to permit reasoning to
continue.

An Assumption should include:

- statement,
- reason,
- scope,
- confidence,
- source,
- validation method,
- expiration condition,
- and consequence if false.

Assumptions must remain visible.

---

# 28. Assumption Budget

A Reasoning Case should maintain an Assumption Budget.

The Assumption Budget limits how much unsupported structure may accumulate
before additional evidence or operator clarification is required.

High-risk decisions should permit fewer or weaker assumptions.

---

# 29. Hidden Assumptions

JARVIS should actively search for hidden assumptions.

Potential hidden assumptions include:

- stable conditions,
- complete data,
- trustworthy sources,
- unchanged policies,
- available resources,
- valid authorization,
- and shared definitions.

A hidden assumption discovered late may invalidate an otherwise coherent
conclusion.

---

# 30. Hypothesis

A Hypothesis is a provisional explanation, diagnosis, or prediction.

A Hypothesis should include:

- hypothesis identifier,
- statement,
- question addressed,
- supporting evidence,
- contradicting evidence,
- assumptions,
- expected observations,
- test method,
- confidence,
- status,
- and competing hypotheses.

Hypotheses are not permanent knowledge.

---

# 31. Hypothesis Generation

Hypothesis Generation should produce plausible alternatives rather than only
the first available explanation.

Generation methods may include:

- rule-based inference,
- analogy,
- causal modeling,
- model-assisted generation,
- historical retrieval,
- anomaly analysis,
- domain heuristics,
- and operator proposals.

Generation should remain separated from evaluation.

---

# 32. Hypothesis Diversity

Material diagnostic or predictive reasoning should consider meaningfully
different hypotheses.

Minor wording variations are not distinct hypotheses.

Diversity may include:

- different causal mechanisms,
- different actors,
- different timelines,
- different constraints,
- and different failure modes.

---

# 33. Null Hypothesis

Where appropriate, JARVIS should consider a null or ordinary explanation.

The architecture should resist unnecessarily exotic conclusions when common
causes remain plausible.

The null hypothesis should not be preferred automatically.

It should be evaluated against evidence.

---

# 34. Hypothesis Testing

Hypothesis Testing compares expected observations against available evidence.

Testing may involve:

- evidence retrieval,
- contradiction search,
- simulation,
- experimentation,
- tool execution,
- historical comparison,
- rule evaluation,
- or operator inquiry.

Tests should preserve method and result.

---

# 35. Hypothesis Lifecycle

Canonical Hypothesis states include:

- proposed,
- screening,
- supported,
- challenged,
- testing,
- validated,
- rejected,
- superseded,
- unresolved,
- and archived.

A validated hypothesis remains subject to future evidence.

---

# 36. Alternative

An Alternative is a possible conclusion, recommendation, or course of action.

Alternatives should be materially distinct.

Each Alternative should include:

- identifier,
- description,
- expected benefit,
- expected cost,
- dependencies,
- assumptions,
- risks,
- reversibility,
- required authority,
- confidence,
- and predicted outcome.

---

# 37. Alternative Generation

Significant decisions should consider more than one plausible Alternative.

Alternative Generation may include:

- status quo,
- delay,
- additional information gathering,
- reversible trial,
- partial execution,
- escalation,
- delegation,
- or abandonment.

Doing nothing is sometimes a valid Alternative and should be explicit.

---

# 38. Alternative Screening

Alternatives may be screened before detailed evaluation.

Screening criteria may include:

- legality,
- policy,
- safety,
- feasibility,
- authority,
- resource availability,
- Mission alignment,
- and deadline compatibility.

Rejected Alternatives should preserve a rejection reason.

---

# 39. Criteria

Decision Criteria define how Alternatives will be compared.

Criteria may include:

- Mission effectiveness,
- accuracy,
- safety,
- cost,
- speed,
- reversibility,
- resilience,
- explainability,
- maintainability,
- operator burden,
- and strategic value.

Criteria should be established before final selection when practical.

---

# 40. Criterion Weight

Criteria may have different importance.

Weights should reflect:

- Mission priority,
- operator direction,
- policy,
- risk,
- and consequence.

Weights must be explainable.

Weights should not be manipulated after evaluation merely to justify a preferred
Alternative.

---

# 41. Tradeoff Analysis

Tradeoff Analysis compares benefits and costs across Alternatives.

Tradeoffs should remain visible.

A recommendation should not imply that a selected Alternative is superior in
every dimension.

Material sacrifices should be communicated.

---

# 42. Constraint

A Constraint limits acceptable reasoning outcomes or actions.

Constraints may include:

- policy,
- law,
- authorization,
- time,
- budget,
- platform,
- safety,
- privacy,
- architecture,
- and operator instruction.

Hard Constraints cannot be violated.

Soft Constraints may be traded off with explicit justification.

---

# 43. Contradiction

A Contradiction exists when two material propositions cannot both be accepted
under the same scope and conditions.

Contradictions may occur between:

- sources,
- claims,
- hypotheses,
- policies,
- Mission objectives,
- Director recommendations,
- or observations.

Contradictions must remain visible until resolved or explicitly tolerated.

---

# 44. Contradiction Record

A Contradiction Record should include:

- contradiction identifier,
- propositions involved,
- source references,
- scope,
- materiality,
- possible explanations,
- resolution state,
- and impact on confidence.

---

# 45. Contradiction Detection

Contradiction Detection may use:

- rules,
- semantic comparison,
- temporal analysis,
- schema validation,
- graph analysis,
- model-assisted review,
- and operator review.

Automated contradiction detection is advisory unless validated by appropriate
logic or evidence.

---

# 46. Contradiction Resolution

Contradictions may be resolved through:

- source authority,
- source freshness,
- scope separation,
- temporal ordering,
- definition clarification,
- additional evidence,
- operator decision,
- or acceptance of unresolved uncertainty.

Resolution must preserve the original contradiction record.

---

# 47. Uncertainty

Uncertainty represents what is not known or not sufficiently supported.

Uncertainty may originate from:

- missing evidence,
- conflicting evidence,
- unreliable sources,
- ambiguous definitions,
- incomplete models,
- environmental variability,
- and future unpredictability.

Uncertainty must not be disguised through confident language.

---

# 48. Uncertainty Classification

Uncertainty may be classified as:

- evidentiary,
- semantic,
- temporal,
- causal,
- predictive,
- operational,
- model-based,
- or authorization-related.

Different uncertainty types require different mitigation strategies.

---

# 49. Confidence

Confidence represents the degree of support for a Claim, Hypothesis,
Alternative, or Decision.

Confidence is not truth.

Confidence should reflect:

- evidence quality,
- evidence quantity,
- evidence independence,
- contradiction,
- assumption burden,
- model reliability,
- domain applicability,
- and temporal relevance.

---

# 50. Confidence Representation

Confidence may be represented through:

- categorical levels,
- numeric ranges,
- probability estimates,
- confidence intervals,
- or structured qualitative assessment.

The representation should match the available evidence.

False precision should be avoided.

---

# 51. Confidence Levels

Canonical qualitative Confidence Levels are:

- negligible,
- low,
- moderate,
- high,
- and very_high.

Each implementation should define operational thresholds.

The label alone is insufficient without supporting rationale.

---

# 52. Confidence Propagation

Derived confidence must account for the weakest material dependencies.

Confidence propagation should consider:

- uncertain assumptions,
- disputed claims,
- evidence dependence,
- contradiction,
- inference depth,
- and model limitations.

A conclusion should not become more certain merely because it is repeated.

---

# 53. Confidence Calibration

Confidence should be calibrated against outcomes.

Calibration evaluates whether:

- high-confidence conclusions are usually correct,
- low-confidence conclusions are appropriately uncertain,
- and systematic overconfidence or underconfidence exists.

Operational Memory should preserve calibration evidence.

---

# 54. Risk

Risk is the combination of possible consequence and uncertainty.

Risk evaluation should consider:

- likelihood,
- impact,
- detectability,
- reversibility,
- exposure,
- time sensitivity,
- and affected parties or systems.

Risk influences verification and authorization.

---

# 55. Risk Record

A Risk Record should include:

- risk identifier,
- description,
- cause,
- consequence,
- likelihood,
- impact,
- confidence,
- mitigation,
- contingency,
- owner,
- and status.

---

# 56. Risk Tolerance

Risk tolerance may be defined by:

- operator preference,
- Mission policy,
- organizational policy,
- legal requirement,
- system mode,
- or delegated authority.

JARVIS should not invent risk tolerance silently.

---

# 57. Reversibility

Reversibility influences recommendation strength.

When confidence is limited, JARVIS should prefer:

- reversible trials,
- checkpoints,
- staged execution,
- backups,
- simulations,
- and validation gates.

Irreversible recommendations require stronger support.

---

# 58. Causal Reasoning

Causal Reasoning evaluates whether one factor contributes to another.

Correlation alone does not establish cause.

Causal reasoning should consider:

- temporal order,
- plausible mechanism,
- alternative causes,
- confounding factors,
- intervention evidence,
- and repeated observation.

Causal claims should identify their evidentiary basis.

---

# 59. Diagnostic Reasoning

Diagnostic Reasoning identifies plausible explanations for observed conditions.

It should consider:

- common explanations,
- severe explanations,
- environmental conditions,
- recent changes,
- failure history,
- and disconfirming evidence.

Diagnostic reasoning should preserve competing hypotheses until adequately
distinguished.

---

# 60. Predictive Reasoning

Predictive Reasoning estimates future states.

Predictions should include:

- time horizon,
- assumptions,
- confidence,
- influencing factors,
- alternative outcomes,
- and indicators to monitor.

Predictions should be updated as new evidence arrives.

---

# 61. Comparative Reasoning

Comparative Reasoning evaluates multiple entities, systems, or actions.

Comparisons require:

- shared criteria,
- consistent scope,
- comparable evidence,
- and explicit tradeoffs.

JARVIS must not compare items using different unstated standards.

---

# 62. Strategic Reasoning

Strategic Reasoning evaluates long-term positioning and consequences.

It should consider:

- objectives,
- competitors,
- dependencies,
- second-order effects,
- resource commitments,
- uncertainty,
- adaptability,
- and future optionality.

Strategic reasoning should distinguish durable advantage from temporary
optimization.

---

# 63. Procedural Reasoning

Procedural Reasoning determines how work should be performed.

It should consider:

- validated procedures,
- prerequisites,
- ordering,
- checkpoints,
- failure recovery,
- verification,
- and authority.

Procedural reasoning feeds the Planning Domain.

It does not execute procedures directly.

---

# 64. Ethical and Policy Reasoning

Reasoning must account for applicable:

- authority,
- policy,
- law,
- safety,
- privacy,
- data classification,
- and operator constraints.

Policy reasoning should cite the controlling rule or policy reference when
available.

---

# 65. Reasoning Strategy

A Reasoning Strategy defines how a Reasoning Case will be evaluated.

Strategies may include:

- rule-based deduction,
- evidence aggregation,
- hypothesis comparison,
- causal analysis,
- constraint satisfaction,
- tradeoff analysis,
- scenario analysis,
- simulation,
- or multi-method evaluation.

The selected strategy should fit the question type.

---

# 66. Strategy Selection

Reasoning Strategy selection should consider:

- question type,
- risk,
- evidence availability,
- time,
- computational cost,
- explainability,
- and required confidence.

A complex strategy is not inherently superior.

The least complex adequate strategy should generally be preferred.

---

# 67. Multi-Method Reasoning

High-impact cases may use multiple independent reasoning methods.

Agreement may increase confidence when methods are genuinely independent.

Disagreement should trigger:

- contradiction analysis,
- evidence review,
- strategy review,
- or escalation.

---

# 68. Model-Assisted Reasoning

Models may assist with:

- question decomposition,
- hypothesis generation,
- evidence summarization,
- contradiction discovery,
- alternative generation,
- and explanation drafting.

Model output is a candidate contribution.

It is not automatically an authoritative conclusion.

---

# 69. Model Independence

No model owns a Reasoning Case.

No model owns permanent claims.

No model owns Mission state.

No model owns verified evidence.

Models are replaceable reasoning resources.

Reasoning continuity must survive model replacement.

---

# 70. Model Selection

Model selection may consider:

- capability,
- latency,
- cost,
- privacy,
- context capacity,
- domain performance,
- availability,
- and historical calibration.

Model selection should remain observable.

---

# 71. Reasoning Director

The Reasoning Director coordinates Reasoning Cases.

Responsibilities include:

- accepting framed reasoning requests,
- selecting Reasoning Strategies,
- requesting evidence,
- coordinating specialized reasoning services,
- maintaining Reasoning Case state,
- managing hypotheses and alternatives,
- initiating verification,
- and returning structured Reasoning Results.

The Reasoning Director coordinates reasoning.

It does not own all reasoning algorithms.

---

# 72. Reasoning Services

Reasoning Services may include:

- Evidence Service,
- Claim Service,
- Hypothesis Service,
- Contradiction Service,
- Confidence Service,
- Risk Service,
- Alternative Service,
- Decision Service,
- Verification Service,
- and Explanation Service.

Each Service should have a narrow contract.

---

# 73. Evidence Service

The Evidence Service manages:

- evidence admission,
- provenance,
- classification,
- quality assessment,
- freshness,
- independence,
- exclusion,
- and evidence gaps.

It does not decide the final conclusion.

---

# 74. Claim Service

The Claim Service manages:

- claim creation,
- support relationships,
- contradiction relationships,
- status,
- dependency,
- and traceability.

It preserves the Claim Graph.

---

# 75. Hypothesis Service

The Hypothesis Service manages:

- generation,
- diversity,
- testing,
- status,
- competition,
- and archival.

It prevents hypotheses from being silently treated as verified facts.

---

# 76. Contradiction Service

The Contradiction Service identifies and tracks material conflict.

It manages:

- contradiction records,
- affected claims,
- resolution attempts,
- materiality,
- and confidence impact.

---

# 77. Confidence Service

The Confidence Service evaluates and propagates confidence.

It should remain:

- transparent,
- configurable,
- calibrated,
- and independent from presentation language.

---

# 78. Risk Service

The Risk Service evaluates consequence and uncertainty.

It supports:

- risk records,
- risk tolerance,
- mitigations,
- contingencies,
- and escalation thresholds.

---

# 79. Alternative Service

The Alternative Service manages:

- alternative generation,
- screening,
- criteria,
- scoring,
- tradeoffs,
- and comparison.

It should preserve rejected Alternatives when materially relevant.

---

# 80. Decision Service

The Decision Service records selected conclusions or recommendations.

It should preserve:

- authority,
- evidence,
- alternatives,
- assumptions,
- confidence,
- risk,
- rationale,
- expected outcome,
- and review condition.

---

# 81. Verification Service

The Verification Service evaluates whether a proposed conclusion is adequately
supported.

Verification may include:

- evidence reinspection,
- independent strategy,
- contradiction search,
- test execution,
- simulation,
- rule validation,
- source validation,
- or operator review.

---

# 82. Explanation Service

The Explanation Service produces operator-facing structured explanations.

It should communicate:

- conclusion,
- supporting evidence,
- material assumptions,
- alternatives considered,
- uncertainty,
- risk,
- and recommended next action.

It should not expose raw private model chain-of-thought.

---

# 83. Reasoning Request

A Reasoning Request should include:

- Mission identifier,
- objective identifier,
- task identifier,
- question,
- question type,
- Cognitive Frame reference,
- constraints,
- authority,
- required confidence,
- deadline,
- risk level,
- and requested output.

---

# 84. Reasoning Result

A Reasoning Result should include:

- case identifier,
- status,
- conclusion or recommendation,
- confidence,
- supporting evidence references,
- contradicting evidence references,
- assumptions,
- alternatives,
- risks,
- unresolved questions,
- verification state,
- explanation,
- and recommended next action.

---

# 85. Decision Record

A Decision Record is the durable record of a significant decision.

It should include:

- decision identifier,
- Reasoning Case identifier,
- Mission identifier,
- question,
- decision,
- decision authority,
- alternatives,
- criteria,
- evidence,
- assumptions,
- contradictions,
- confidence,
- risks,
- expected outcome,
- timestamp,
- review condition,
- and supersession state.

---

# 86. Decision Authority

Decision authority may belong to:

- the operator,
- standing policy,
- delegated autonomy,
- a Director,
- or an external authority.

The Reasoning Architecture may recommend.

It must not silently expand its own authority.

---

# 87. Recommendation

A Recommendation proposes an action or conclusion without claiming final
authority.

Recommendations should identify:

- recommended Alternative,
- reason,
- confidence,
- risks,
- assumptions,
- and required authorization.

---

# 88. Inconclusive Result

A Reasoning Case may conclude as inconclusive.

An inconclusive result should identify:

- what remains unknown,
- why available evidence is insufficient,
- what evidence would help,
- risk of acting,
- risk of waiting,
- and recommended next step.

Inconclusive reasoning is preferable to false certainty.

---

# 89. Escalation

A Reasoning Case should escalate when:

- authority is insufficient,
- risk exceeds tolerance,
- evidence remains materially conflicted,
- required confidence cannot be reached,
- policy requires review,
- or the consequence exceeds delegated autonomy.

Escalation should preserve the complete case record.

---

# 90. Self-Verification

Self-Verification checks a Reasoning Result before release or execution.

Verification depth should scale with:

- consequence,
- irreversibility,
- uncertainty,
- novelty,
- contradiction,
- and operator requirements.

---

# 91. Verification Levels

Canonical Verification Levels are:

- none,
- basic,
- standard,
- elevated,
- and critical.

Examples:

- Basic may recheck evidence references.

- Standard may include contradiction search.

- Elevated may use an independent method or model.

- Critical may require deterministic tests and operator authorization.

---

# 92. Independent Verification

Independent Verification should avoid reusing the exact same unsupported
reasoning path.

Independence may involve:

- a different method,
- a different model,
- a deterministic rule,
- a test,
- a simulation,
- a separate evidence set,
- or an operator.

---

# 93. Verification Failure

If verification fails, the Reasoning Case should not remain silently decided.

Possible outcomes include:

- return to evidence collection,
- revise assumptions,
- generate new hypotheses,
- reduce confidence,
- mark inconclusive,
- or escalate.

---

# 94. Explanation

An Explanation communicates why a conclusion is reasonable.

A useful Explanation should answer:

- What is the conclusion?
- What evidence supports it?
- What evidence challenges it?
- What assumptions were required?
- What alternatives were considered?
- How confident is JARVIS?
- What risks remain?
- What should happen next?

---

# 95. Explanation Depth

Explanation depth may be:

- summary,
- operational,
- analytical,
- or audit.

The operator may request deeper detail.

The same authoritative Reasoning Case should support every explanation depth.

---

# 96. Structured Rationale

JARVIS should preserve structured rationale rather than raw hidden
chain-of-thought.

Structured rationale includes:

- evidence references,
- assumptions,
- decision criteria,
- alternative comparison,
- confidence,
- risk,
- and concise justification.

This is sufficient for accountability and inspection.

---

# 97. Chain-of-Thought Boundary

Raw private model reasoning is not an architectural record.

The system should not depend on storing verbatim hidden model deliberation.

Instead, JARVIS should persist:

- inputs,
- evidence,
- claims,
- hypotheses,
- alternatives,
- tests,
- decisions,
- confidence,
- and structured explanation.

---

# 98. Reasoning Observability

Operators should be able to inspect:

- active Reasoning Cases,
- current status,
- evidence gaps,
- unresolved contradictions,
- pending verification,
- confidence,
- risk,
- and decisions awaiting authority.

Observability should not expose sensitive internal implementation details.

---

# 99. Reasoning Events

Canonical Reasoning Events may include:

- reasoning_case_created,
- question_clarified,
- evidence_admitted,
- evidence_excluded,
- evidence_gap_detected,
- claim_created,
- contradiction_detected,
- hypothesis_proposed,
- hypothesis_rejected,
- alternative_created,
- evaluation_completed,
- verification_requested,
- verification_failed,
- recommendation_issued,
- decision_recorded,
- case_escalated,
- and case_closed.

---

# 100. Event Ownership

Reasoning Events describe state transitions.

The Reasoning Case remains authoritative.

An event stream should not become a second competing source of truth.

---

# 101. Operational Memory Integration

Completed Reasoning Cases may contribute to Operational Memory.

Persisted experience may include:

- decision outcome,
- confidence calibration,
- evidence quality,
- failed hypotheses,
- effective verification methods,
- and lessons learned.

Operational Memory should not convert every past decision into permanent truth.

---

# 102. Knowledge Domain Integration

Verified external facts belong to the Knowledge Domain.

Reasoning may produce candidate knowledge.

Candidate knowledge must pass the appropriate Knowledge verification and
assimilation process before becoming authoritative knowledge.

Reasoning does not write directly into permanent knowledge.

---

# 103. Planning Domain Integration

The Reasoning Architecture may recommend a course of action.

The Planning Domain converts an approved recommendation into:

- objectives,
- tasks,
- dependencies,
- resources,
- checkpoints,
- and contingencies.

Reasoning owns justification.

Planning owns future operational structure.

---

# 104. Execution Domain Integration

The Execution Domain performs authorized work.

Execution results return as observations and evidence.

Execution does not rewrite the original Reasoning Case.

New evidence may cause a new case version or a superseding case.

---

# 105. Reflection Domain Integration

Reflection evaluates whether:

- reasoning was correct,
- confidence was calibrated,
- assumptions were valid,
- alternatives were adequate,
- risks were identified,
- and verification was effective.

Reflection produces lesson candidates.

---

# 106. Communication Domain Integration

The Communication Domain presents Reasoning Results.

It may adapt:

- language,
- depth,
- format,
- modality,
- and visualization.

Presentation changes must not alter the authoritative decision record.

Communication owns presentation.

Reasoning owns structured justification.

---

# 107. Mission Control Integration

Mission Control may display:

- active Reasoning Cases,
- evidence status,
- hypothesis status,
- alternative comparisons,
- confidence,
- risk,
- decisions,
- and verification state.

Mission Control renders backend Reasoning State.

It does not create independent reasoning truth.

---

# 108. Commander Brief Integration

The Commander Brief may summarize:

- important decisions,
- unresolved questions,
- high-risk assumptions,
- pending operator decisions,
- significant contradictions,
- and recommended next actions.

The Commander Brief should prioritize operational relevance over reasoning
detail.

---

# 109. Reasoning Persistence

Reasoning Cases must be durably persisted when they affect:

- Mission decisions,
- authorization,
- execution,
- policy,
- safety,
- long-running operations,
- or future learning.

Low-value temporary reasoning may be discarded after required summaries are
preserved.

---

# 110. Reasoning Versioning

A Reasoning Case should support versioning.

New evidence may:

- update a case,
- reopen a case,
- supersede a decision,
- or create a related case.

Historical versions must remain available for audit.

---

# 111. Reasoning Immutability

Completed Decision Records should be immutable.

Corrections should create:

- amendments,
- superseding decisions,
- or linked correction records.

Historical reasoning should not be silently rewritten.

---

# 112. Reasoning Privacy

Reasoning records may contain sensitive:

- Mission context,
- evidence,
- personal data,
- policy information,
- or operational details.

Access should follow:

- authorization,
- data classification,
- least privilege,
- retention policy,
- and audit requirements.

---

# 113. Reasoning Security

Reasoning inputs may be manipulated.

Threats include:

- poisoned evidence,
- malicious instructions,
- forged provenance,
- prompt injection,
- compromised tools,
- misleading duplication,
- and fabricated authority.

Reasoning must preserve trust boundaries.

---

# 114. Untrusted Content

Untrusted content should be treated as evidence, not instruction.

Retrieved documents, webpages, messages, and tool output must not silently
override:

- Mission intent,
- system policy,
- authorization,
- or architectural constraints.

---

# 115. Evidence Poisoning

Potential evidence poisoning indicators include:

- inconsistent provenance,
- unusual duplication,
- impossible timestamps,
- authority mismatch,
- unexplained formatting changes,
- contradictory metadata,
- and coordinated unsupported claims.

Suspected poisoning should reduce confidence and trigger verification.

---

# 116. Reasoning Degradation

When preferred reasoning resources are unavailable, JARVIS should degrade
explicitly.

Possible degraded modes include:

- reduced evidence retrieval,
- reduced model capability,
- rule-only evaluation,
- local-only evidence,
- reduced alternative generation,
- and mandatory operator review.

Degraded reasoning must not masquerade as normal capability.

---

# 117. Offline Reasoning

Offline reasoning may use:

- local models,
- local Knowledge,
- cached Operational Memory,
- deterministic rules,
- local evidence,
- and deferred verification.

Offline limitations should remain visible in Reasoning Results.

---

# 118. Distributed Reasoning

Reasoning may be distributed across devices or services.

Distributed reasoning requires:

- stable case identity,
- explicit ownership,
- authority boundaries,
- synchronized evidence references,
- event ordering,
- conflict resolution,
- and durable final authority.

Only one authoritative Decision Record should exist for a decision version.

---

# 119. Reasoning Performance

Reasoning performance should not be measured only by latency.

Measures may include:

- correctness,
- evidence quality,
- confidence calibration,
- contradiction discovery,
- alternative quality,
- decision usefulness,
- verification success,
- operator burden,
- and outcome quality.

---

# 120. Reasoning Quality

Reasoning Quality should consider:

- relevance,
- correctness,
- completeness,
- traceability,
- consistency,
- uncertainty handling,
- risk handling,
- explainability,
- and operational usefulness.

---

# 121. Reasoning Evaluation

Evaluation should include deterministic and scenario-based tests.

Scenarios should test:

- missing evidence,
- contradictory evidence,
- stale evidence,
- duplicated evidence,
- hidden assumptions,
- high-risk decisions,
- inconclusive results,
- verification failure,
- Director disagreement,
- and degraded operation.

---

# 122. Calibration Evaluation

Calibration tests should compare:

- stated confidence,
- actual outcome,
- evidence quality,
- and decision category.

Systematic overconfidence must be treated as a defect.

---

# 123. Explainability Evaluation

Explainability tests should determine whether an operator can identify:

- the conclusion,
- supporting evidence,
- assumptions,
- alternatives,
- uncertainty,
- risks,
- and decision authority.

A fluent answer without these elements is not sufficiently explainable for a
significant decision.

---

# 124. Reasoning Invariants

The following invariants must remain true:

1. Every Reasoning Case belongs to a Cognitive Frame.

2. Every material conclusion preserves evidence references.

3. Observations remain distinguishable from inferences.

4. Assumptions remain explicit.

5. Contradictions remain visible until resolved.

6. Significant decisions consider Alternatives.

7. Confidence reflects evidence and uncertainty.

8. High-risk conclusions receive stronger verification.

9. Recommendations do not silently grant execution authority.

10. Models remain replaceable.

11. Raw hidden chain-of-thought is not an architectural dependency.

12. Mission Control does not own authoritative reasoning state.

13. Reasoning does not write directly into permanent Knowledge.

14. Completed Decision Records are not silently rewritten.

15. Inconclusive results are valid outcomes.

---

# 125. Prohibited Patterns

The following patterns violate this architecture:

- accepting fluent language as evidence,
- treating model output as authoritative by default,
- storing inference as verified fact,
- hiding assumptions,
- discarding contradicting evidence,
- inventing confidence without rationale,
- selecting an Alternative before defining criteria,
- repeatedly retrying the same reasoning path without change,
- exposing raw private chain-of-thought as the explanation mechanism,
- coupling reasoning permanently to one model,
- allowing UI state to become authoritative reasoning state,
- silently changing Decision Records,
- and claiming certainty when evidence is insufficient.

---

# 126. Minimum Reasoning Contract

The minimum Reasoning Request contract should include:

- case identifier,
- Mission identifier,
- question,
- question type,
- Cognitive Frame reference,
- constraints,
- authority,
- risk level,
- and requested output.

The minimum Reasoning Result contract should include:

- status,
- conclusion,
- confidence,
- evidence references,
- assumptions,
- alternatives,
- risks,
- verification state,
- explanation,
- and recommended next action.

---

# 127. Implementation Sequence

Implementation should proceed in controlled stages:

1. Reasoning contracts and enumerations.

2. Reasoning Case state model.

3. Evidence Record and Evidence Service.

4. Claim and Claim Graph models.

5. Assumption model and Assumption Budget.

6. Hypothesis lifecycle.

7. Alternative and Criteria models.

8. Contradiction detection contracts.

9. Confidence evaluation and propagation.

10. Risk evaluation.

11. Decision Records.

12. Verification Service.

13. Explanation Service.

14. Reasoning Director.

15. Reasoning event stream.

16. Operational Memory integration.

17. Mission Control observability API.

18. Scenario-based verification.

Implementation must not bypass the invariants defined in this document.

---

# 128. Initial Package Boundary

The expected future package boundary is:

reasoning/
├── __init__.py
├── contracts.py
├── enums.py
├── errors.py
├── cases/
├── evidence/
├── claims/
├── assumptions/
├── hypotheses/
├── alternatives/
├── contradictions/
├── confidence/
├── risk/
├── decisions/
├── verification/
├── explanation/
├── director/
└── events/
# 129. Relationship to Phase IX-C

Phase IX-B defines how JARVIS reaches and explains conclusions.

Phase IX-C will define how approved conclusions become operational plans.

Canonical handoff:

Reasoning Result

↓

Approved Recommendation

↓

Planning Request

↓

Objectives

↓

Tasks

↓

Dependencies

↓

Execution Plan

Reasoning decides what appears justified.

Planning decides how approved intent should be realized.

130. Acceptance Criteria

Phase IX-B is architecturally complete when:

Reasoning Cases are defined,
evidence and provenance are defined,
claims and Claim Graphs are defined,
assumptions are explicit,
hypotheses have a lifecycle,
Alternatives and Criteria are defined,
contradictions are preserved,
confidence and propagation are defined,
risk influences verification,
Decision Records are immutable,
structured explanations are defined,
raw chain-of-thought is excluded as an architectural dependency,
model independence is preserved,
Director and Service boundaries are defined,
Knowledge, Planning, Execution, Reflection, and UI boundaries are preserved,
invariants are explicit,
and implementation remains technology-independent.

# 130. Acceptance Criteria

Phase IX-B is architecturally complete when:

- Reasoning Cases are formally defined.
- Evidence and provenance are explicitly represented.
- Claims remain distinguishable from observations.
- Assumptions are explicit and auditable.
- Hypotheses have a managed lifecycle.
- Alternatives are generated and evaluated.
- Contradictions are preserved until resolved.
- Confidence reflects evidence quality rather than language fluency.
- Risk influences verification depth.
- Decision Records are immutable after completion.
- Structured explanations are produced without exposing private model chain-of-thought.
- Model independence is preserved.
- The Reasoning Director coordinates rather than monopolizes reasoning.
- Knowledge, Planning, Execution, Reflection, and Communication boundaries remain explicit.
- Mission Control renders reasoning state without becoming the authoritative owner.
- Architectural invariants remain enforceable.
- Technology choices remain replaceable without altering reasoning doctrine.

Successful completion of this phase establishes the permanent architectural
contract governing how JARVIS transforms evidence into defensible operational
judgment.

# 131. Guiding Doctrine

JARVIS should be able to answer:

What question was considered?
What evidence was used?
Where did the evidence come from?
What assumptions were made?
What alternatives were considered?
What contradictions remain?
How confident is the conclusion?
What risks exist?
How was the conclusion verified?
Who possesses decision authority?
What should happen next?

A conclusion that cannot answer these questions is not sufficiently governed for
significant operational use.

# 132. Conclusion

Reasoning is not eloquence.

Reasoning is not model output.

Reasoning is not certainty.

Reasoning is the disciplined transformation of evidence into defensible
judgment.

JARVIS preserves observations.

JARVIS evaluates evidence.

JARVIS exposes assumptions.

JARVIS considers alternatives.

JARVIS detects contradictions.

JARVIS communicates uncertainty.

JARVIS verifies important conclusions.

JARVIS records decisions.

JARVIS learns from outcomes.

Knowledge is permanent.

Intelligence is upgradable.

Experience is cumulative.

Judgment is earned.

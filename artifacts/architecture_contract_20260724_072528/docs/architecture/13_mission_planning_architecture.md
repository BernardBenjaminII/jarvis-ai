# JARVIS Mission Planning Architecture

**Phase:** IX-C  
**Status:** Canonical Architecture  
**Authority:** ADR-0000  
**Depends On:** Cognitive Architecture and Explainable Reasoning Architecture  
**Successor Phase:** IX-D Executive Control Architecture  

---

# 1. Purpose

This document defines the canonical architecture through which JARVIS converts
reasoned judgment into controlled operational plans.

The planning system transforms:

- accepted objectives,
- evidence-backed recommendations,
- commander intent,
- operational constraints,
- available capabilities,
- known risks,
- dependencies,
- authorization boundaries,
- environmental conditions,
- and mission history

into structured plans that may be:

- reviewed,
- challenged,
- approved,
- simulated,
- scheduled,
- executed,
- monitored,
- revised,
- suspended,
- resumed,
- completed,
- or terminated.

Planning is the bridge between cognition and action.

Planning does not replace:

- reasoning,
- authorization,
- execution,
- mission ownership,
- human judgment,
- or executive control.

The planner determines how an approved objective could be achieved.

It does not independently decide whether the objective should be pursued or
whether execution is authorized.

---

# 2. Architectural Position

The canonical cognitive-operational flow is:

Knowledge
    ↓
Reasoning
    ↓
Planning
    ↓
Authorization
    ↓
Execution
    ↓
Observation
    ↓
Reflection
    ↓
Operational Memory
Each layer has a distinct responsibility.

2.1 Knowledge

Knowledge supplies:

source material,
factual records,
capabilities,
historical outcomes,
environmental context,
policies,
constraints,
and prior mission experience.

Knowledge does not produce binding operational decisions.

2.2 Reasoning

Reasoning evaluates:

what is known,
what is uncertain,
what is inferred,
what alternatives exist,
what risks are present,
and what course of action appears justified.

Reasoning produces recommendations and judgments.

It does not directly execute actions.

2.3 Planning

Planning converts accepted reasoning into an operational structure.

It determines:

desired outcomes,
intermediate objectives,
tasks,
activities,
dependencies,
sequencing,
capability requirements,
resource requirements,
checkpoints,
fallback actions,
completion criteria,
and termination conditions.

Planning produces proposals for controlled action.

2.4 Authorization

Authorization determines whether a plan or plan step may proceed.

Authorization may be provided by:

the Commander,
a delegated authority,
a policy engine,
an approval workflow,
an established standing order,
or an explicitly bounded automation rule.

Authorization must be distinguishable from planning.

2.5 Execution

Execution performs approved actions through registered capabilities.

Execution must not silently reinterpret the mission.

2.6 Observation

Observation captures:

action results,
state changes,
external events,
errors,
deviations,
incomplete outcomes,
and newly discovered information.
2.7 Reflection

Reflection compares expected results with observed results.

It determines whether:

the plan remains valid,
assumptions were incorrect,
risk has changed,
replanning is required,
execution should continue,
or the mission should be escalated.
2.8 Operational Memory

Operational memory preserves:

plans,
approvals,
revisions,
decisions,
outcomes,
failures,
explanations,
and lessons learned.

This allows future planning to improve without silently rewriting history.

# 3. Mission Planning Philosophy

JARVIS mission planning follows several permanent principles.

3.1 Intent Before Procedure

A plan must begin with commander intent.

Commander intent defines:

why the mission exists,
what outcome matters,
what must be preserved,
what must be avoided,
and what tradeoffs are acceptable.

A sequence of tasks without intent is not a complete mission plan.

3.2 Outcomes Before Actions

Planning must define the desired outcome before selecting actions.

The planner must not confuse:

Performing an action with:

Achieving an objective

A successful command does not necessarily produce a successful mission.

3.3 Plans Are Proposals

A generated plan is a structured proposal until it is authorized.

The existence of a plan must never imply authorization to execute it.

3.4 Explainability Is Mandatory

Every material planning decision must be explainable.

JARVIS must be able to answer:

Why is this task necessary?
What objective does it support?
What evidence influenced it?
What assumptions does it depend on?
What alternatives were considered?
Why was this sequence selected?
What could cause the plan to fail?
What requires human approval?
3.5 Uncertainty Must Remain Visible

Planning must preserve uncertainty rather than converting uncertainty into
false confidence.

Plans may contain:

confirmed facts,
supported estimates,
working assumptions,
unresolved questions,
confidence levels,
and explicit information gaps.
3.6 Authority Must Be Explicit

Every executable element must have an authorization requirement.

The requirement may be:

no execution allowed,
commander approval required,
delegated approval allowed,
policy approval allowed,
standing authorization present,
or automatic execution allowed within defined limits.

No task may inherit unlimited authority merely because its parent mission was
approved.

3.7 Execution Must Be Bounded

Plans must define operational boundaries.

Examples include:

approved directories,
approved systems,
approved networks,
approved devices,
approved contacts,
approved tools,
time windows,
cost limits,
data-handling restrictions,
rate limits,
and geographic boundaries.
3.8 Replanning Is Normal

A plan is not assumed to remain correct after execution begins.

Planning must support revision when:

evidence changes,
resources become unavailable,
tasks fail,
priorities change,
risks increase,
authorization changes,
or the operational environment changes.

3.9 Human Control Must Be Preserved

JARVIS must support meaningful human intervention.

The Commander must be able to:

inspect the plan,
challenge assumptions,
alter objectives,
reject tasks,
modify boundaries,
approve or deny execution,
pause the mission,
resume the mission,
and terminate the mission.

3.10 Safety Overrides Optimization

The shortest or fastest plan is not automatically the best plan.

Safety, legality, integrity, reversibility, privacy, and authority take
precedence over convenience or speed.

3.11 Mission History Is Immutable

Approved and executed plan versions must remain historically traceable.

A revised plan must create a new version.

It must not overwrite the record of what was previously approved or executed.

# 4. Canonical Mission Hierarchy

The canonical hierarchy is:

Mission
    └── Objective
            └── Task
                    └── Activity
                            └── Command

This hierarchy is authoritative across:

backend services,
persistence,
APIs,
user interfaces,
audit logs,
planning tools,
and execution systems.

Alternative labels may be displayed in specialized interfaces, but the
underlying canonical model must remain stable.

4.1 Mission

A mission is the highest operational unit.

A mission defines:

commander intent,
desired end state,
mission scope,
governing constraints,
authorization model,
risk posture,
priority,
ownership,
lifecycle state,
and completion conditions.

A mission may contain one or more objectives.

Example:

Mission:
Prepare the Salé residence for an extended vacancy while preserving security,
utilities, structural condition, and remote observability.

A mission is not simply a folder for tasks.

It is an authoritative operational context.

4.2 Objective

An objective defines a measurable result required to achieve the mission.

An objective must describe an outcome rather than merely an activity.

Weak objective:

Check the apartment.

Strong objective:

Verify that water, electricity, ventilation, access control, and monitoring
systems are configured for six months of safe vacancy.

An objective may depend on other objectives.

An objective may contain one or more tasks.

4.3 Task

A task is a bounded unit of work that contributes to an objective.

A task defines:

expected output,
responsible capability or actor,
prerequisites,
constraints,
authorization requirement,
validation method,
failure handling,
and completion criteria.

Example:

Task:
Inspect all plumbing fixtures and isolate nonessential water lines.

Tasks should be independently observable and auditable.

4.4 Activity

An activity is an operational step within a task.

Activities provide enough structure to guide execution without requiring every
implementation detail to be embedded in the mission definition.

Example:

Activity:
Photograph the water meter before closing the main valve.

Activities may be performed by:

a human,
a JARVIS capability,
a connected device,
a software service,
or a coordinated combination of actors.
4.5 Command

A command is the lowest canonical executable unit.

A command may represent:

a shell invocation,
an API call,
a tool invocation,
a device instruction,
a database operation,
a message,
a file operation,
or another concrete action.

Commands must remain subordinate to the activity, task, objective, and mission
that authorize them.

Example:

Command:
Capture a timestamped image from camera living-room-01.

A command must never become the primary unit of mission reasoning.

Commands are implementation details of an approved operational plan.

# 5. Planning Actors and Responsibilities

Mission planning is coordinated across several architectural actors.

The canonical relationship is:

Commander
    ↓
Executive Director
    ↓
Mission Planning Director
    ↓
Reasoning Director
    ↓
Knowledge Director
    ↓
Capability Directors
    ↓
Execution Services

These relationships represent responsibility boundaries rather than mandatory
process boundaries.

A single runtime may initially host several responsibilities, but their
contracts must remain separate.

5.1 Commander

The Commander is the highest mission authority.

The Commander:

defines or accepts mission intent,
establishes priorities,
provides constraints,
approves sensitive plans,
modifies authorization,
resolves escalated conflicts,
and may suspend or terminate any mission.

The Commander may be:

the primary user,
an explicitly delegated human authority,
or a future authorized command structure.

The Commander is not treated as a passive prompt source.

Commander intent is persistent mission context.

5.2 Executive Director

The Executive Director owns cross-mission coordination.

The Executive Director:

receives commander intent,
establishes mission context,
assigns planning responsibility,
resolves priority conflicts,
coordinates directors,
enforces executive policy,
requests authorization,
monitors mission health,
and decides when escalation is required.

The Executive Director does not personally generate every task or command.

It delegates planning to the Mission Planning Director.

5.3 Mission Planning Director

The Mission Planning Director owns the planning lifecycle.

It is responsible for:

creating planning sessions,
gathering planning inputs,
generating candidate plans,
evaluating plan completeness,
coordinating risk analysis,
identifying capability requirements,
identifying authorization requirements,
constructing plan versions,
validating plan structure,
submitting plans for approval,
revising plans,
and preserving planning history.

The Mission Planning Director must not execute plan commands directly.

It produces execution-ready plans for authorized execution services.

5.4 Reasoning Director

The Reasoning Director supplies judgments that support planning.

It may provide:

problem decomposition,
causal analysis,
option generation,
tradeoff analysis,
hypothesis evaluation,
confidence estimates,
contradiction detection,
and recommendations.

The Reasoning Director explains what appears justified.

The Mission Planning Director converts that judgment into operational form.

5.5 Knowledge Director

The Knowledge Director supplies evidence and context.

It may provide:

source retrieval,
mission history,
policies,
technical references,
capability documentation,
environmental context,
prior outcomes,
known hazards,
and unresolved knowledge gaps.

The Knowledge Director does not authorize action.

5.6 Capability Directors

Capability Directors describe what JARVIS can actually do.

Examples may include:

Knowledge Acquisition Director,
Cybersecurity Director,
Device Director,
Communications Director,
Software Development Director,
Vision Director,
Voice Director,
Home Operations Director,
and Platform Director.

A Capability Director provides:

capability identity,
supported operations,
required inputs,
expected outputs,
operational constraints,
risk classification,
authorization requirements,
execution environment,
and health status.

Planning must use registered capability contracts rather than assuming a tool
exists or behaves in a particular way.

5.7 Execution Services

Execution Services perform authorized activities and commands.

They are responsible for:

validating authorization,
confirming execution boundaries,
invoking capabilities,
recording results,
returning structured observations,
reporting errors,
and supporting cancellation where possible.

Execution Services must reject plan elements that exceed their authorization
or capability boundaries.

# 6. Planning Inputs

A planning session must receive structured inputs.

The minimum planning input model is:

PlanningInput
├── mission_intent
├── desired_end_state
├── objectives
├── known_facts
├── assumptions
├── constraints
├── prohibitions
├── available_capabilities
├── unavailable_capabilities
├── resource_limits
├── time_constraints
├── risk_tolerance
├── authorization_context
├── dependencies
├── prior_mission_context
└── unresolved_questions
6.1 Mission Intent

Mission intent states why the mission exists and what must be achieved.

It should include:

purpose,
desired outcome,
priority,
preserved values,
and acceptable tradeoffs.
6.2 Desired End State

The desired end state defines the observable condition that indicates mission
success.

It must be more precise than a general aspiration.

Example:

All identified services are safely configured for extended vacancy, monitoring
is operational, access is controlled, and a verified re-entry checklist is
stored in JARVIS.
6.3 Known Facts

Known facts are claims accepted as sufficiently supported for planning.

Every material fact should preserve provenance where available.

6.4 Assumptions

Assumptions are claims temporarily treated as true so planning can proceed.

Every assumption must include:

its description,
why it is needed,
confidence,
validation method,
impact if false,
and expiration condition where applicable.
6.5 Constraints

Constraints define limits within which the plan must operate.

Examples:

budget,
time,
platform,
geography,
privacy,
policy,
available personnel,
available hardware,
network access,
and data residency.
6.6 Prohibitions

Prohibitions identify actions that must not occur.

Examples:

do not delete source files,
do not contact external parties,
do not execute destructive commands,
do not expose private information,
do not scan systems outside the authorized network,
and do not spend money without approval.

Prohibitions must be represented explicitly rather than inferred from absence.

6.7 Available Capabilities

Available capabilities must be resolved from the capability registry.

A planning session should know:

capability name,
capability version,
current availability,
supported platform,
required permissions,
risk class,
and expected reliability.
6.8 Resource Limits

Resource limits may include:

memory,
CPU,
GPU,
storage,
network bandwidth,
power,
API quotas,
financial budget,
human availability,
and time.
6.9 Risk Tolerance

Risk tolerance defines how aggressively JARVIS may pursue the mission.

The canonical initial values are:

minimal
low
moderate
elevated
critical

These values describe acceptable operational exposure.

They do not describe the severity of a discovered hazard.

6.10 Authorization Context

Authorization context identifies:

who may approve the plan,
what is pre-authorized,
what requires explicit approval,
what may never be delegated,
and when authorization expires.
6.11 Prior Mission Context

Prior mission context may include:

previous plan versions,
prior outcomes,
incomplete tasks,
abandoned approaches,
previous approvals,
and lessons learned.

A planner should not repeatedly propose a failed approach without acknowledging
the prior result.

6.12 Unresolved Questions

Unresolved questions are information gaps that may affect planning.

Each question should indicate whether it is:

blocking,
important but non-blocking,
optional,
or suitable for resolution during execution.
# 7. Canonical Planning Pipeline

The canonical planning pipeline is:

Intent Capture
    ↓
Context Assembly
    ↓
Objective Formation
    ↓
Constraint Resolution
    ↓
Capability Resolution
    ↓
Option Generation
    ↓
Risk Evaluation
    ↓
Plan Construction
    ↓
Dependency Analysis
    ↓
Authorization Mapping
    ↓
Plan Validation
    ↓
Simulation or Review
    ↓
Approval Submission
    ↓
Approved Plan Version

Each stage produces structured output.

The planner must preserve the intermediate record required to explain how the
final plan was produced.

7.1 Intent Capture

Intent capture converts a request into persistent mission intent.

The output must distinguish:

stated intent,
inferred intent,
unresolved ambiguity,
and planner interpretation.

Inferred intent must never be silently represented as directly stated intent.

7.2 Context Assembly

Context assembly gathers:

relevant knowledge,
operating conditions,
policies,
system state,
capability state,
mission history,
and authorization context.

Context must be scoped to the mission.

Unrelated knowledge must not be added merely because it is available.

7.3 Objective Formation

Objective formation converts the desired end state into measurable objectives.

Objectives must be:

outcome-oriented,
bounded,
testable,
traceable to intent,
and assigned completion criteria.
7.4 Constraint Resolution

Constraint resolution identifies conflicts among:

objectives,
time,
resources,
policy,
risk tolerance,
available capabilities,
and commander instructions.

Unresolved constraint conflicts must block plan approval or be explicitly
escalated.

7.5 Capability Resolution

Capability resolution identifies which registered capabilities could perform
the required work.

The planner must verify:

availability,
compatibility,
authority,
platform support,
and operational boundaries.

A capability name alone is insufficient.

7.6 Option Generation

The planner should generate alternative approaches where material choices
exist.

Each option should identify:

expected benefits,
expected costs,
risks,
dependencies,
reversibility,
required authorization,
and confidence.

The planner may select a preferred option but must preserve meaningful rejected
alternatives when they influenced the decision.

7.7 Risk Evaluation

Risk evaluation identifies:

operational hazards,
safety risks,
security risks,
privacy risks,
legal or policy concerns,
mission failure conditions,
capability failure conditions,
and cascading effects.

Risk evaluation must occur before plan approval.

7.8 Plan Construction

Plan construction creates the canonical hierarchy:

Mission
    → Objectives
        → Tasks
            → Activities
                → Commands

Each element must be traceable to its parent purpose.

7.9 Dependency Analysis

Dependency analysis determines:

execution order,
prerequisites,
parallelizable work,
blocking conditions,
external dependencies,
and recovery paths.

Circular dependencies must invalidate the plan.

7.10 Authorization Mapping

Authorization mapping assigns an authorization policy to every executable
element.

Examples:

planning_only
commander_approval
delegated_approval
policy_approval
standing_authorization
automatic_within_bounds
prohibited

A parent approval may satisfy a child requirement only when the policy
explicitly allows inheritance.

7.11 Plan Validation

Plan validation checks:

schema validity,
hierarchy integrity,
objective coverage,
task completeness,
dependency consistency,
authorization coverage,
capability availability,
boundary completeness,
risk documentation,
rollback availability,
and completion criteria.

A structurally invalid plan must not proceed to execution.

7.12 Simulation or Review

Plans may be evaluated through:

static review,
policy review,
dependency simulation,
resource simulation,
dry-run execution,
adversarial critique,
red-team review,
or commander inspection.

The required review depth depends on mission risk.

7.13 Approval Submission

The planner submits a specific immutable plan version for approval.

Approval must reference:

mission identifier,
plan identifier,
plan version,
approving authority,
approval scope,
authorization boundaries,
expiration,
and any conditions.

Approval of one plan version does not automatically approve later revisions.

# 8. Planning State Model

The canonical planning states are:

draft
context_gathering
awaiting_information
candidate
under_review
revision_required
awaiting_approval
approved
scheduled
active
replanning
suspended
completed
failed
terminated
archived
8.1 Draft

The planning session exists but is incomplete.

A draft may be freely revised.

It is not executable.

8.2 Context Gathering

JARVIS is collecting the information required to construct the plan.

This may include:

knowledge retrieval,
capability discovery,
policy checks,
environmental observation,
and commander clarification.

8.3 Awaiting Information

The planner cannot proceed responsibly without additional information.

The planning record must identify:

the missing information,
why it is required,
who may supply it,
and whether partial planning can continue.

8.4 Candidate

A candidate plan is structurally complete enough for evaluation.

It has not yet passed all review or authorization gates.

8.5 Under Review

The plan is being evaluated by one or more reviewers.

Reviewers may include:

the Commander,
the Executive Director,
policy services,
safety services,
capability directors,
or specialized reviewers.

8.6 Revision Required

The plan was reviewed and must be changed before approval.

The reasons for revision must be preserved.

8.7 Awaiting Approval

The plan has passed required validation and is waiting for authorization.

It must remain immutable while approval is pending.

Any change creates a new plan version and invalidates the pending approval
request.

8.8 Approved

A specific plan version has received the required authorization.

Approved does not necessarily mean execution has started.

8.9 Scheduled

The plan is approved and assigned an execution window or trigger.

8.10 Active

At least one authorized plan element is currently executing or awaiting its
next execution condition.

8.11 Replanning

Observed conditions require material modification of the approved plan.

During replanning:

unsafe execution must pause,
unaffected bounded work may continue only when explicitly allowed,
and revised actions require appropriate approval.

8.12 Suspended

The mission is temporarily prevented from continuing.

Suspension may result from:

commander action,
missing resources,
increased risk,
policy conflict,
capability failure,
or environmental change.

8.13 Completed

All required mission completion conditions have been satisfied and validated.

Completion requires outcome verification, not merely task exhaustion.

8.14 Failed

The mission cannot achieve its required end state under the current plan and
constraints.

Failure must preserve:

the failed conditions,
completed work,
remaining state,
observed causes,
and possible recovery options.

8.15 Terminated

An authorized actor deliberately ended the mission before successful
completion.

Termination must record:

authority,
reason,
timestamp,
final state,
and required cleanup actions.

8.16 Archived

The mission is no longer operational but remains available for audit,
historical retrieval, and learning.

# 9. Canonical State Transitions

The normal planning path is:

draft
    ↓
context_gathering
    ↓
candidate
    ↓
under_review
    ↓
awaiting_approval
    ↓
approved
    ↓
scheduled
    ↓
active
    ↓
completed
    ↓
archived

Common alternate transitions include:

context_gathering → awaiting_information
awaiting_information → context_gathering

under_review → revision_required
revision_required → candidate

active → replanning
replanning → awaiting_approval
replanning → active

active → suspended
suspended → active
suspended → terminated

active → failed
failed → archived

any_nonfinal_state → terminated
completed → archived
terminated → archived

Invalid transitions must be rejected by the planning service.

Examples of invalid transitions:

draft → active
candidate → scheduled
awaiting_approval → completed
archived → active
terminated → approved

# 10. Planning Invariants

The following rules are permanent planning invariants.

Every task must belong to exactly one objective.
Every activity must belong to exactly one task.
Every command must belong to exactly one activity.
Every objective must trace to mission intent.
Every executable element must have an authorization policy.
Every executable element must identify its capability requirement.
Every task must define completion criteria.
Every approved plan must have an immutable version identifier.
Every plan revision must create a new version.
Every assumption must remain distinguishable from fact.
Every material risk must have an owner or treatment decision.
Every dependency must reference an existing plan element.
Dependency cycles are prohibited.
Every active mission must have an authorized plan version.
Execution must stop when authorization expires or is revoked.
Completion must be validated against the desired end state.
Plan history must never be silently overwritten.
Commands may not expand their own scope.
Capabilities may not grant themselves authority.
Planning output must remain explainable.

# 11. Initial Service Boundaries

The initial implementation should preserve the following service boundaries:

MissionService
PlanningService
PlanRepository
PlanningSessionService
PlanValidationService
DependencyService
AuthorizationMappingService
RiskPlanningService
CapabilityResolutionService
PlanExplanationService

These may initially exist in a shared package, but their responsibilities must
remain separable.

A suggested package direction is:

core/
└── executive/
    └── planning/
        ├── __init__.py
        ├── contracts.py
        ├── models.py
        ├── states.py
        ├── errors.py
        ├── repository.py
        ├── service.py
        ├── validation.py
        ├── dependencies.py
        ├── authorization.py
        ├── capability_resolution.py
        ├── risk.py
        └── explanation.py

This package path is architectural guidance.

The exact implementation path may be adjusted during Phase IX-C implementation,
provided the public contracts and responsibility boundaries remain consistent
with this document.

# 12. Phase IX-C Part 1 Completion Boundary

This first architecture section establishes:

the purpose of mission planning,
its position between reasoning and execution,
the permanent planning principles,
the canonical mission hierarchy,
planning actors,
planning inputs,
the planning pipeline,
planning states,
state transitions,
planning invariants,
and initial service boundaries.

The continuation of this document will define:

canonical planning data contracts,
plan versioning,
dependency representation,
risk treatment,
authorization gates,
resource planning,
simulation,
replanning,
failure recovery,
persistence,
API boundaries,
Director integration,
execution handoff,
observability,
and acceptance criteria.
# 13. Canonical Declaration

Mission planning is the controlled transformation of commander intent and
reasoned judgment into explainable, bounded, reviewable, and authorizable
operational structure.

No plan is authority.

No command is a mission.

No successful action alone proves a successful outcome.

JARVIS must preserve the distinction between:

thinking,
planning,
authorizing,
acting,
observing,
and learning.

That distinction is foundational to trustworthy executive intelligence.

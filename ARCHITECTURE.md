# JARVIS Architecture Constitution

**Document authority:** Repository-level architectural constitution  
**Applies to:** All production code, tests, documentation, development tools,
interfaces, and future contributors  
**Change policy:** Architectural review and an accepted ADR are required for
substantive changes

---

# 1. Identity

JARVIS is an Executive Operating System.

Its purpose is to transform reliable knowledge into:

1. justified conclusions;
2. explainable decisions;
3. executable plans;
4. accountable actions;
5. durable institutional memory.

JARVIS is not defined by any single language model, inference provider,
interface, device, operating system, or deployment environment.

Models and runtime technologies are replaceable capabilities. The architecture
is the enduring system.

---

# 2. Constitutional Motto

> Knowledge is permanent. Intelligence is upgradable.

Knowledge, provenance, evidence, decisions, and institutional memory must
remain durable even when models, algorithms, hardware, and interfaces change.

---

# 3. Architectural Principles

## 3.1 Evidence before belief

JARVIS must not silently promote ungrounded statements into accepted knowledge.

## 3.2 Claims before hypotheses

Evidence supports or opposes explicit propositions. Hypotheses are constructed
from claims and relationships, not directly from unstructured text.

## 3.3 Determinism before optimization

Equivalent canonical inputs must produce equivalent canonical identities and
results whenever the operation is defined as deterministic.

## 3.4 Explainability before autonomy

The system must be able to account for the evidence, assumptions, policies,
authority, and reasoning supporting consequential conclusions and actions.

## 3.5 Architecture before implementation

New capabilities must have a defined layer, boundary, responsibility, and
verification strategy before becoming production dependencies.

## 3.6 Reliability before capability

A smaller certified capability is preferable to a broader capability whose
behavior, provenance, or failure modes cannot be verified.

## 3.7 Explicit uncertainty

Confidence, uncertainty, contradiction, insufficiency, and unresolved
questions must be represented explicitly rather than concealed.

## 3.8 Human authority is explicit

Execution authority must be represented through policy and governance. It may
not be inferred merely because an action is technically possible.

---

# 4. Cognitive Pipeline

The canonical cognitive progression is:

Knowledge Source
      ↓
Representation
      ↓
Observation
      ↓
Evidence
      ↓
Claim
      ↓
Relationship
      ↓
Hypothesis
      ↓
Interpretation
      ↓
Reasoning
      ↓
Justification
      ↓
Planning
      ↓
Executive Decision
      ↓
Mission
      ↓
Authorized Action
      ↓
Outcome and Institutional Memory
Each layer must preserve the information needed to trace its outputs to prior
layers.

A higher layer may depend on lower layers. Lower layers may not depend on
higher layers.

---

# 5. Layer Responsibilities
5.1 Knowledge

Owns durable source material, catalogs, collections, acquisition state,
integrity, and retrieval.

5.2 Representation

Transforms source material into stable machine-processable structures while
preserving provenance and source boundaries.

5.3 Observation

Records explicit extracted or observed content. Observation does not decide
whether a proposition is true.

5.4 Evidence

Associates observations and provenance with explicit support, opposition,
context, exclusion, or absence.

5.5 Claims

Constructs normalized propositions whose evidence state is explicit.

5.6 Relationships

Represents explicit relationships among claims and other cognitive objects.

5.7 Hypotheses

Constructs and compares possible explanations or predictions grounded in
claims and relationships.

5.8 Interpretation

Assigns contextual meaning to supported or contested hypotheses.

5.9 Reasoning

Applies defined reasoning methods to cognitive objects without assuming
executive authority.

5.10 Justification

Produces auditable explanation structures connecting conclusions to their
support, opposition, assumptions, methods, and policies.

5.11 Planning

Transforms approved reasoning outcomes into possible objectives, tasks, and
execution plans.

5.12 Executive

Selects, governs, authorizes, rejects, pauses, or escalates plans and actions.

5.13 Mission

Tracks authorized objectives, tasks, activities, commands, outcomes, and
accountability.

---

# 6. Dependency Constitution

Dependencies must flow forward:

common
  ↓
observation
  ↓
evidence
  ↓
claims
  ↓
relationships
  ↓
hypotheses
  ↓
interpretation
  ↓
reasoning
  ↓
justification

The following are forbidden unless an accepted ADR explicitly authorizes an
exception:

cognition importing API or UI implementations;
observation importing evidence or claims;
evidence importing claims or hypotheses;
claims importing hypotheses or interpretation;
lower cognitive layers importing executive or planning implementations;
circular imports among cognition layers;
production code importing development verification modules;
direct access to another subsystem's private implementation.

Cross-subsystem communication must use stable public contracts.

---

# 7. Public API Constitution

Stable public APIs are exported through subsystem facades.

For cognition, the canonical consumer interface is:

from core.cognition import Observation
from core.cognition import EvidenceRecord
from core.cognition import ClaimRecord

Consumers should not depend on internal module locations unless explicitly
documented as an internal extension point.

Internal implementations may move while stable facade imports remain valid.

A public API removal or incompatible semantic change requires:

an accepted ADR;
a migration path;
deprecation documentation;
regression tests;
an intentional version change.

---

# 8. Deterministic Cognitive Objects

Cognitive objects declared deterministic must:

use canonical normalized content;
use stable serialization;
use deterministic identifiers;
reject conflicting supplied identifiers;
remain immutable after construction;
preserve source and parent references;
produce equivalent identities regardless of irrelevant input ordering.

Random identifiers must not replace content-derived identities for canonical
cognitive objects.

---

# 9. Repository Responsibilities
core/

Stable production runtime and domain architecture.

tests/

Executable specifications of required behavior, contracts, regressions, and
architectural boundaries.

docs/

Durable project knowledge, architecture, decisions, procedures, and design
rationale.

dev/

Development, installation, migration, audit, and verification utilities. Code
under dev/ must not become a production runtime dependency.

api/

External application interfaces and transport contracts. API code must call
stable subsystem interfaces rather than private implementations.

ui/

Human interaction surfaces. UI code must not own core domain behavior.

---

# 10. Development Constitution

A production capability is incomplete until it has:

a defined architectural responsibility;
complete implementation files;
unit tests;
regression coverage where applicable;
structural verification;
architecture documentation;
an ADR when architectural policy changes;
deterministic verification output;
a clean Git state after certification.

Code generation installers are not the canonical source of production files.

Production source files must exist directly under version control. Installers
and verification scripts may validate, migrate, or configure those files, but
must not conceal the authoritative implementation inside large shell
here-documents.

---

# 11. Change Discipline

Before introducing a new subsystem, contributors must answer:

What problem does it solve that the present architecture cannot?
At which architectural layer does the responsibility belong?
Which lower layers may it depend upon?
Which higher layers must remain inaccessible?
What is its stable public contract?
How will correctness and boundaries be verified?
Can it be removed or replaced without corrupting durable knowledge?

If those answers are unclear, implementation must not begin.

---

# 12. Documentation Authority

Documentation categories have distinct authority:

ARCHITECTURE.md defines repository-wide constitutional principles.
ADRs record binding architectural decisions and their rationale.
architecture documents define subsystem structures and boundaries.
phase documents describe implementation milestones.
runbooks describe repeatable operational procedures.
whitepapers explain broader theory and design philosophy.
tests define executable behavioral requirements.

Lower-authority documents may elaborate upon, but may not silently contradict,
higher-authority documents.

---

# 13. Verification Philosophy

Verification must test more than successful execution.

Where applicable, certification must include:

package compilation;
stable imports;
public API compatibility;
package topology;
forbidden dependency detection;
circular dependency detection;
deterministic identity;
immutability;
input-order independence;
contradiction preservation;
regression tests;
documentation completeness;
ADR synchronization.

A green verifier certifies only the properties it actually tests.

No verification output may claim broader assurance than the implemented checks
provide.

---

# 14. Evolution

JARVIS must be designed so that the following can evolve independently:

language models;
inference engines;
embedding models;
storage engines;
operating systems;
user interfaces;
hardware platforms;
local and remote execution providers;
acquisition methods;
domain specialists.

Durable knowledge and cognitive provenance must not be locked to a replaceable
runtime technology.

---

# 15. Ultimate Standard

A consequential JARVIS conclusion should eventually support the question:

Show exactly why this conclusion was reached.

A consequential JARVIS action should eventually support the question:

Show the evidence, reasoning, authority, policy, and accountable decision
that permitted this action.

That traceability is a foundational capability, not an optional presentation
feature.

# ADR-0020: Genesis IV Cognition Architecture Constitution

**Status:** Accepted  
**Date:** 2026-07-21  
**Decision scope:** Cognition subsystem structure and evolution  
**Supersedes:** No earlier ADR  
**Related:** ADR-0018, ADR-0019

---

# Context

The Genesis IV cognition implementation has established observation,
provenance, evidence, evidence-chain, and claim capabilities.

Those capabilities were initially developed as flat modules under:

```text
core/cognition/

That structure supported rapid incremental construction, but it will not scale
cleanly as relationships, hypotheses, interpretation, justification, and
reasoning are added.

A large flat package would:

obscure architectural boundaries;
make dependency direction harder to enforce;
increase the probability of circular imports;
make ownership of validation and contracts ambiguous;
make future migration more disruptive;
encourage consumers to depend on implementation locations.

The subsystem therefore requires a permanent layered package topology before
additional cognitive capabilities are introduced.

Decision

The cognition subsystem shall adopt this permanent internal topology:

core/cognition/
├── common/
├── observation/
├── evidence/
├── claims/
├── relationships/
├── hypotheses/
├── interpretation/
├── justification/
└── reasoning/

The module:

core/cognition/__init__.py

shall remain the canonical stable facade for public cognition imports.

Migration shall occur incrementally. Each layer will be moved in a dedicated,
independently verified package.

Genesis IV-R0 Package A creates the destination topology but does not move
existing production implementations.

Dependency Direction

The canonical dependency direction is:

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

A layer may depend on approved lower layers.

A lower layer may not import a higher layer.

Cognition implementation modules may not depend on:

UI implementations;
API transport implementations;
executive implementations;
planning implementations;
development verification code.

Exceptions require a separate accepted ADR.

Public API Stability

The following style remains canonical:

from core.cognition import Observation
from core.cognition import EvidenceRecord
from core.cognition import ClaimRecord

Implementation paths may change during R0, but facade imports and semantics
must remain stable.

Compatibility re-export modules may be maintained temporarily when required
for internal or external callers.

Migration Packages
R0-A

Repository skeleton and architectural constitution.

R0-B

Common infrastructure migration.

R0-C

Observation-layer migration.

R0-D

Evidence-layer migration.

R0-E

Claims-layer migration.

R0-F

Public API and dependency certification.

R0-G

Documentation consolidation and final R0 certification.

Consequences
Positive
package structure reflects the cognitive model;
layer ownership becomes explicit;
dependency direction can be verified;
future cognitive capabilities receive permanent homes;
the public facade isolates consumers from implementation movement;
migration risk is divided into small certifiable increments.
Costs
flat modules and subpackages temporarily coexist;
compatibility imports may exist during migration;
each migration requires regression verification;
the reorganization temporarily delays new feature development.
Risks

A migration could accidentally:

change deterministic identities;
alter normalization;
break public imports;
create circular dependencies;
duplicate class identities by loading old and new implementations
independently.

Each migration package must therefore move one architectural layer at a time
and certify object identity, serialization, imports, and existing behavior.

Rejected Alternatives
Continue using a flat package

Rejected because anticipated cognition growth would produce weak ownership and
increasing import complexity.

Move every module in one operation

Rejected because a large atomic refactor would make failures harder to isolate
and rollback.

Break the public API and require consumers to use internal paths

Rejected because implementation locations should not become permanent
consumer contracts.

Duplicate implementations during migration

Rejected because duplicate class definitions could produce incompatible type
identities and divergent behavior.

Compatibility layers must re-export the canonical implementation rather than
copying it.

Verification

R0 certification must eventually verify:

required topology;
facade stability;
import direction;
absence of circular dependencies;
singular canonical class identities;
deterministic identity preservation;
immutable contract preservation;
regression behavior;
documentation completeness.

Genesis IV-R0 Package A verifies topology and unchanged facade behavior before
any implementation is moved.

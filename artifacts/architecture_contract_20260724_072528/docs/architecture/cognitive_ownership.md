# Canonical Cognitive Subsystem Ownership

**Status:** Accepted architecture baseline  
**Release:** Genesis IV-R3A Pack 3  
**Purpose:** Define canonical ownership boundaries for JARVIS cognitive domain models.

## 1. Governing Principle

Each cognitive concept has exactly one canonical owning subsystem.

Other subsystems may consume, reference, adapt, or serialize that concept, but
they must not independently redefine its domain model.

This rule prevents competing truths while allowing controlled compatibility
migrations.

## 2. Canonical Ownership Map

| Concept family | Canonical owner | Primary consumers |
| --- | --- | --- |
| Observation and observed facts | `core.cognition.layers.observation` | Evidence, reasoning, representation |
| Evidence and propositions | `core.evidence` | Reasoning, cognition, executive |
| Reasoning, inference, and hypotheses | `core.reasoning` | Executive, mission planning |
| Cognitive representation and segmentation | `core.representation` | Cognition, reasoning, knowledge |
| Missions, objectives, tasks, and plans | `core.executive` | API, UI, runtime |
| Presentation and interaction state | UI layer | Human operator |

## 3. Ownership Rules

1. The owning subsystem defines the canonical contracts, enums, errors, and
   serialization guarantees for its concepts.
2. Consumers import canonical types rather than reproducing equivalent types.
3. Compatibility aliases may exist temporarily during migration.
4. Compatibility aliases must be explicitly documented and tested.
5. No legacy module may be removed while active imports or serialized-data
   compatibility obligations remain.
6. Migration changes imports and ownership; it does not rewrite proven
   algorithms without a separate architectural reason.
7. Circular ownership is prohibited.

## 4. Canonical Evidence Ownership

`core.evidence` is the canonical owner of:

- `Proposition`
- `EvidenceRecord`
- `EvidenceAssessment`
- `EvidenceRelationship`
- evidence lifecycle enums
- evidence-domain errors
- canonical evidence serialization

`core.reasoning` may evaluate or consume evidence but must not remain the
long-term owner of evidence-domain contracts.

`core.cognition` may construct cognitive workflows involving evidence but must
not maintain a competing evidence domain model.

## 5. Controlled Migration Protocol

Every ownership migration follows these gates:

1. **Inventory** — identify duplicate symbols and every consumer.
2. **Canonical declaration** — name the permanent owner.
3. **Compatibility design** — determine aliases, adapters, or data migration.
4. **Import migration** — redirect consumers in bounded, verified packs.
5. **Compatibility verification** — prove public behavior remains valid.
6. **Legacy quarantine** — freeze the old implementation against new features.
7. **Removal eligibility** — confirm zero active imports and no unresolved
   persistence obligations.
8. **Removal certification** — delete only in a dedicated certified pack.

## 6. Current Migration Direction

```text
core/reasoning/evidence  ─────┐
                              ├──> core/evidence
core/cognition evidence ──────┘
```

The arrow represents canonical ownership migration, not immediate deletion.

## 7. Prohibited Actions

Until migration eligibility is certified, do not:

- delete `core/reasoning/evidence`;
- bulk-rewrite reasoning algorithms;
- silently alias semantically different enums;
- change serialized field names;
- merge contracts solely because their names match;
- add new evidence capabilities to legacy evidence packages.

## 8. Completion Condition

The Evidence ownership migration is complete when:

- all production consumers use `core.evidence` directly or through an approved
  compatibility adapter;
- duplicate evidence contracts no longer evolve independently;
- all compatibility tests pass;
- persisted representations remain readable or have a certified migration;
- the legacy package is proven removable.

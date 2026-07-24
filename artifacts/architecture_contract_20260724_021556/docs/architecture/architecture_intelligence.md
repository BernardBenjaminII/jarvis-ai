# JARVIS Architecture Intelligence

**Status:** Genesis V-A1 foundation  
**Canonical package:** `core.architecture`

## 1. Mission

Architecture Intelligence provides deterministic, machine-readable models for
describing, analyzing, governing, and certifying the JARVIS repository.

It exists to answer questions such as:

- What subsystems exist?
- Which subsystem owns a concept?
- What depends on what?
- Which public symbols are duplicated?
- Are two implementations compatible?
- What blocks a migration?
- Has a certified architecture drifted?
- Is a release ready for certification?

## 2. Separation of Responsibilities

`core.architecture` contains stable domain contracts and deterministic
primitives.

Repository scanning, Git inspection, report generation, and release tooling
remain under `dev/architecture` or `dev/verification`.

Production subsystems must not depend on development tooling.

## 3. Foundation Contracts

Genesis V-A1 introduces:

- `ArchitectureSnapshot`
- `SubsystemDefinition`
- `ModuleDefinition`
- `PublicSymbol`
- `DependencyEdge`
- `OwnershipDeclaration`
- `ArchitectureFinding`
- `CompatibilityAssessment`
- `MigrationPlan`
- `MigrationStep`
- `CertificationRecord`

These contracts are immutable and canonically serializable.

## 4. Deterministic Fingerprints

Every architecture contract can produce:

- canonical compact JSON;
- deterministic SHA-256 fingerprints.

Dictionary ordering, set ordering, enum serialization, dataclass field
serialization, tuples, lists, and paths are normalized deterministically.

## 5. Safety Boundary

Genesis V-A1 does not:

- scan the repository;
- modify source files;
- write Git state;
- delete packages;
- redirect imports;
- perform runtime orchestration;
- autonomously approve migrations.

It defines the vocabulary used by later Architecture Intelligence packs.

## 6. Planned Packs

- **V-A2:** Repository inventory engine.
- **V-A3:** Ownership registry and policy manifest.
- **V-B1:** Dependency governance.
- **V-B2:** Semantic equivalence analysis.
- **V-B3:** Migration planning.
- **V-C1:** Certification manifests.
- **V-C2:** Release readiness.
- **V-C3:** Architecture drift detection.

## 7. Governing Principle

Architecture Intelligence may observe, analyze, explain, and recommend.

Human authority approves source changes, migrations, deletions, and releases.

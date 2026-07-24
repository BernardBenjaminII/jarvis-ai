# Executive Integration Acceptance Criteria

## System-wide criteria

- [ ] Every top-level subsystem appears in the integration matrix.
- [ ] Every visible metric has a real data provider.
- [ ] Every capability has a registry descriptor.
- [ ] Every executable UI action reaches a real command handler.
- [ ] Every command returns a normalized result envelope.
- [ ] Every command produces an audit/timeline event.
- [ ] Every failure state is visible.
- [ ] Every unavailable capability includes a reason.
- [ ] Every knowledge-backed answer can expose sources.
- [ ] Every confidence score exposes its basis.
- [ ] Every missing-knowledge judgment exposes its evidence.
- [ ] The UI contains no hard-coded claim that a subsystem is operational.
- [ ] API schemas are versioned.
- [ ] OpenAPI is regression-tested.
- [ ] Read projections are safe and idempotent.
- [ ] Destructive commands require explicit semantics.
- [ ] UI and API accessibility tests pass.
- [ ] Master verification passes with zero failures.

## Definition of integrated

A subsystem is **fully integrated** only when all are true:

1. package exists;
2. service/facade exists;
3. health provider exists;
4. projection exists;
5. API route exists;
6. schema test exists;
7. capability descriptors exist;
8. UI surface exists;
9. commands are bound where applicable;
10. audit/timeline events are emitted;
11. verification script covers the path.

## Certification result

Genesis UI-A may be marked complete only when the audit reports zero:

- backend-only critical capabilities;
- UI placeholders;
- unbound primary actions;
- undocumented metrics;
- silent failures.

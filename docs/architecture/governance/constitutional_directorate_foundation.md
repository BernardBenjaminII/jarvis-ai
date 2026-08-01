# Genesis VII-C4.3 Pack 3B-2B.1 — Directorate Foundation

## Mission

Establish the canonical organizational vocabulary and deterministic foundation for the JARVIS directorate projection.

## Scope

Pack 3B-2B.1 introduces:

- canonical directorates;
- organizational root;
- canonical responsibilities;
- repository ownership domains;
- directorate node and edge contracts;
- deterministic fingerprints;
- integrity verification.

It does not yet assign ownership domains to directorates. That belongs to Pack 3B-2B.2.

## Canonical directorates

- Executive Directorate
- Governance Directorate
- Knowledge Directorate
- Reasoning Directorate
- Software Engineering Directorate
- Planning Directorate
- Operations Directorate
- Intelligence Acquisition Directorate

## Node kinds

- `directorate`
- `responsibility`
- `ownership_domain`
- `organizational_unit`

## Edge kinds

- `owns`
- `supervises`
- `responsible_for`
- `maintains`
- `operates`
- `certifies`

Pack 3B-2B.1 materializes `supervises` and `responsible_for`. The remaining relationships are reserved for Pack 3B-2B.2.

## Upstream fingerprint chain

Pack 3B-2B.1 preserves:

- article intelligence fingerprint;
- graph foundation fingerprint;
- authority graph fingerprint;
- repository projection fingerprint.

## Integrity rules

- all canonical directorates exist;
- node IDs are unique;
- edge IDs are unique;
- no dangling edges;
- supervisory edges connect the organization root to directorates;
- responsibility edges connect directorates to responsibilities;
- no responsibilities are orphaned.

## Canonical artifact

`artifacts/audit/km0000-c4_3-pack3b2b1/constitutional_directorate_foundation.json`

## Next phase

Pack 3B-2B.2 should add:

- deterministic ownership assignment;
- ownership and maintenance relationships;
- directorate graph queries;
- directorate metrics;
- projection reporting.

# Genesis VII-C4.3 Pack 3B-2B.3 — Executive Governance

## Mission

Transform the certified Directorate Projection into a deterministic executive decision service.

## Capabilities

The service resolves repository owner, maintainers, certifiers, reviewers, affected domains, affected capabilities, unresolved paths, and deterministic impact fingerprints.

## Canonical API

- `owner(path)`
- `maintainers(path)`
- `certifiers(path)`
- `reviewers(path)`
- `executive_summary(path)`
- `impact.assess(paths)`

## Resolution semantics

Authority resolution uses the longest matching repository ownership-domain path.

## Canonical artifacts

`artifacts/audit/km0000-c4_3-pack3b2b3/`

- `constitutional_executive_governance.json`
- `constitutional_executive_governance_summary.md`

## Boundary

This pack certifies the service layer. UI and route integration remain downstream work.

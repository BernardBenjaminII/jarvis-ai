# Convergence C-6 — Executive Observability & Mission Transparency

C-6 exposes the converged Executive execution path through deterministic,
UI-safe projections. It does not expose hidden chain-of-thought. It publishes
observable stages, mission/director activation, evidence and gap counts,
answerability, confidence, contradictions, and the latest mission timeline.

## Public surface

- `core.observability.ExecutiveObservabilityService`
- conversation metadata key `mission_transparency`
- conversation metadata marker `observability=executive_mission_transparency`
- `GET /operations/transparency`

## Boundary

Observability consumes public execution artifacts only. It does not own mission,
knowledge, evidence, or reasoning state and does not alter Executive decisions.

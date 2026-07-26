# Genesis IV-B4 — Observation Audit Correction

## Purpose

Correct the convergence audit so architectural ownership is assigned only to
modules that directly define `class Observation`.

## Distinctions

1. **Definition** — contains a direct `class Observation`.
2. **Public export** — imports or re-exports `Observation`.
3. **Adapter** — converts another representation into canonical Observation.
4. **Migration entry** — governs a true noncanonical definition.

`core/cognition/contracts.py` is a public API surface, not an Observation
owner. Its export is inventoried separately and is not registered as a legacy
definition.

## Certification Rule

A public import or re-export must never create a second architectural owner.

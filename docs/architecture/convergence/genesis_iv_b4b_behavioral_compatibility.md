# Genesis IV-B4B — Behavioral Compatibility Certification

## Mission

Certify that the Observation migration layer preserves the observable behavior
of the Genesis IV-B3 compatibility surface while retaining IV-B4 governance.

## Certified Behaviors

- `core/cognition/contracts.py` remains approved legacy.
- Historical operational observations continue to map to `PLATFORM`.
- Mission and correlation identifiers remain first-class context fields.
- Unknown Observation definitions remain forbidden.
- IV-B3, IV-B4, IV-B4A, and IV-B4A.1 remain regression gates.

## Rule

Migration may normalize representation, but it may not silently alter domain
classification or operational context.

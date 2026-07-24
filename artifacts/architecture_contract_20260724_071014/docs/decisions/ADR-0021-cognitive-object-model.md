# ADR-0021: Establish the Cognitive Object Model

**Status:** Accepted  
**Decision date:** 2026-07-21

Introduce `core/cognition/common/object_model.py` as the shared immutable object
foundation for future cognition layers. Existing public APIs remain unchanged in
R1. The model provides deterministic serialization and hashing, but its hash is
an audit aid rather than an authorization token or digital signature.

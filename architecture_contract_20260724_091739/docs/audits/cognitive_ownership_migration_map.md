# Cognitive Ownership Migration Map

**Canonical evidence owner:** `core.evidence`  
**Legacy evidence package:** `core.reasoning.evidence`  
**Removal eligible:** NO

## 1. Legacy Package Files

- `core/reasoning/evidence/__init__.py`
- `core/reasoning/evidence/contracts.py`
- `core/reasoning/evidence/enums.py`
- `core/reasoning/evidence/errors.py`
- `core/reasoning/evidence/identifiers.py`
- `core/reasoning/evidence/serialization.py`
- `core/reasoning/evidence/validation.py`

## 2. Active Legacy Imports

| Consumer | Legacy imports |
| --- | --- |
| None | None |

## 3. Active Canonical Imports

| Consumer | Canonical imports |
| --- | --- |
| None | None |

## 4. Duplicate Symbols Touching `core.evidence`

| Symbol | Locations |
| --- | --- |
| `AssessmentMethod` | `core/evidence/enums.py`<br>`core/reasoning/evidence/enums.py` |
| `EvidenceAssessment` | `core/evidence/contracts.py`<br>`core/reasoning/evidence/contracts.py` |
| `EvidenceDirection` | `core/cognition/evidence.py`<br>`core/evidence/enums.py` |
| `EvidenceError` | `core/evidence/errors.py`<br>`core/reasoning/evidence/errors.py` |
| `EvidenceRecord` | `core/cognition/evidence.py`<br>`core/evidence/contracts.py`<br>`core/reasoning/evidence/contracts.py` |
| `EvidenceRelationship` | `core/evidence/contracts.py`<br>`core/reasoning/evidence/contracts.py` |
| `EvidenceRelationshipError` | `core/evidence/errors.py`<br>`core/reasoning/evidence/errors.py` |
| `EvidenceRelationshipType` | `core/evidence/enums.py`<br>`core/reasoning/evidence/enums.py` |
| `EvidenceSerializationError` | `core/evidence/errors.py`<br>`core/reasoning/evidence/errors.py` |
| `EvidenceStatus` | `core/evidence/enums.py`<br>`core/reasoning/evidence/enums.py` |
| `EvidenceValidationError` | `core/evidence/errors.py`<br>`core/reasoning/evidence/errors.py` |
| `Proposition` | `core/evidence/contracts.py`<br>`core/representation/contracts.py` |
| `StableStringEnum` | `core/evidence/enums.py`<br>`core/reasoning/evidence/enums.py` |
| `utc_now` | `core/cognition/common/object_model.py`<br>`core/cognition/layers/observation/models.py`<br>`core/cognition/workspace/models.py`<br>`core/evidence/contracts.py`<br>`core/executive/models.py`<br>`core/executive/planning/models.py`<br>`core/knowledge_catalog/assimilation/engine.py`<br>`core/knowledge_catalog/collections.py`<br>`core/knowledge_catalog/models.py`<br>`core/knowledge_catalog/registrar.py` |

## 5. Migration Decision

The legacy package is not removable while any of the following remain:

- production imports of `core.reasoning.evidence`;
- semantically unresolved duplicate contracts;
- persisted payloads tied to the legacy schema;
- compatibility obligations without adapters.

This audit authorizes analysis only. It does not authorize deletion.

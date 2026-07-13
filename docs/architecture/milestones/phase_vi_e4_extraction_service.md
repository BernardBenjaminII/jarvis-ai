# JARVIS Gen 2 — Phase VI-E4

# Extraction and Chunking Service

**Status:** Complete

---

# Purpose

Phase VI-E4 completes the separation of document extraction responsibilities
from the Assimilation Runner.

Prior to this phase, the Runner contained knowledge of how documents were
opened, normalized, hashed, and divided into chunks.

After Phase VI-E4, the Runner functions purely as an orchestration component,
delegating extraction to a dedicated service while preserving existing
behavior.

This phase improves modularity, testability, dependency injection, and future
extensibility.

---

# Motivation

The Assimilation Runner had accumulated several unrelated responsibilities.

It previously coordinated:

- work selection
- transaction management
- extraction
- normalization
- checksum generation
- chunk generation
- persistence
- attempt journaling
- lifecycle transitions

Extraction logic represented an independent concern and therefore violated
the Single Responsibility Principle.

Phase VI-E4 introduces a dedicated Extraction Service.

---

# Architectural Change

## Before

```text
AssimilationRunner
    ├── validate path
    ├── read document
    ├── normalize text
    ├── checksum
    ├── chunk text
    ├── persist
    ├── update attempts
    └── update lifecycle
```

## After

```text
AssimilationRunner
    ├── claim work
    ├── delegate extraction
    ├── delegate persistence
    ├── delegate attempt journaling
    ├── delegate state transitions
    └── coordinate transaction

                    │

                    ▼

           ExtractionService
                ├── validate path
                ├── detect format
                ├── read document
                ├── normalize
                ├── checksum
                └── chunk
```

---

# New Component

## ExtractionService

Location

```text
knowledge_engine/assimilation/services/extraction.py
```

Responsibilities

- validate source paths
- perform format-aware extraction
- normalize extracted text
- generate deterministic checksum
- generate deterministic chunks
- return immutable extraction result
- identify extractor used

Does NOT

- open database connections
- begin transactions
- commit transactions
- modify registry
- modify queue
- write document records
- journal attempts

---

# ExtractionResult

The service returns an immutable value object.

Fields

- document_path
- extractor
- normalized_text
- checksum
- chunks

Derived Properties

- text_chars
- chunk_count
- usable

This object is intentionally immutable to prevent accidental mutation during
assimilation.

---

# Runner Changes

The Runner now owns orchestration only.

Extraction occurs through dependency injection.

Example

```python
extraction = self.extraction_service.extract(
    document_path=str(path),
)
```

The returned object is passed directly to:

- DocumentPersistenceService
- AttemptJournalService
- AssimilationStateService

---

# Responsibilities After Phase VI-E4

## AssimilationRunner

Owns

- work selection
- workflow orchestration
- transaction coordination
- success/failure workflow
- service composition

Does NOT own

- extraction
- normalization
- checksum generation
- chunk generation

---

## ExtractionService

Owns

- source validation
- extraction
- normalization
- checksum
- chunk generation
- extractor metadata

---

# Dependency Injection

The Runner constructor now accepts

```python
extraction_service: ExtractionService | None = None
```

Default construction

```python
self.extraction_service = (
    extraction_service
    or ExtractionService()
)
```

This allows unit testing without modifying Runner logic.

---

# Preserved Behavior

Phase VI-E4 intentionally preserves

- TXT extraction
- Markdown extraction
- existing PDF extraction
- checksum algorithm
- chunk ordering
- chunk overlap
- retry behavior
- persistence behavior
- attempt journaling
- lifecycle transitions

No functional regression is expected.

---

# Verification

Focused verification

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_phase_6e4.sh
```

Master verification

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_all.sh
```

---

# Engineering Contracts

Phase VI-E4 guarantees

✓ ExtractionService owns extraction

✓ Runner contains no direct extraction implementation

✓ Extraction results remain immutable

✓ Extractor metadata reaches persistence

✓ Attempt statistics remain consistent

✓ Lifecycle transitions remain unchanged

✓ Existing functionality preserved

---

# Exit Criteria

Phase VI-E4 is complete when

- ExtractionService compiles successfully
- Focused verification passes
- Master verification passes
- Runner delegates extraction
- No direct extraction logic remains in Runner
- Documentation completed
- Historical milestone committed independently
- Changes pushed to GitHub

---

# Historical Notes

Phase VI-E4 represents the completion of the service-oriented refactoring of
the Assimilation Runner.

With extraction, persistence, attempt journaling, and lifecycle transitions
all delegated to dedicated services, the Runner becomes a true orchestration
component.

This architectural separation enables future capabilities—including new
extractors, additional document formats, distributed processing, and
parallel assimilation—without requiring structural changes to the Runner.

Phase VI-E4 serves as the final service extraction milestone before the
architecture contract phases (VI-F), which formalize and enforce these
boundaries through automated verification.

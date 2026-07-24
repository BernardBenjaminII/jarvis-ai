# JARVIS Gen 2 Assimilation Core

## Purpose

The Assimilation Core converts external knowledge objects into verified,
chunked, searchable knowledge ready for embedding.

---

## High-Level Flow

Knowledge Object
        ↓
Director
        ↓
Handler Registry
        ↓
Handler
        ↓
Extraction Service
        ↓
Persistence Service
        ↓
Attempt Journal
        ↓
State Service
        ↓
Ready for Embedding

---

## Components

### AssimilationRunner

Responsibilities:
- orchestration only
- no SQL business logic
- no extraction logic

### ExtractionService

Responsibilities:
- document extraction
- normalization
- checksum generation
- chunk creation

### DocumentPersistenceService

Responsibilities:
- document_text
- chunks

### AttemptJournalService

Responsibilities:
- attempt history
- diagnostics

### AssimilationStateService

Responsibilities:
- registry transitions
- queue transitions

### HandlerRegistry

Responsibilities:
- object_type dispatch

### Handlers

single_document

source_collection

---

## Future Handlers

pdf_collection

web_site

git_repository

youtube_channel

wiki_dump

api_dataset

...

---

## Design Rules

Services never call each other.

Runner coordinates.

Handlers own object behavior.

Director owns scheduling.

Database transactions remain inside Runner.

Services are transaction-neutral.

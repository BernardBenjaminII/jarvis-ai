# JARVIS Gen 2 — Phase VII-A1

# Knowledge Acquisition Foundation

**Status:** Complete after focused verification, master verification, and
successful milestone push.

---

## Purpose

Phase VII-A1 introduces the first acquisition layer above the frozen
assimilation core.

The phase discovers local source candidates and produces deterministic,
immutable acquisition plans.

It does not download, admit, assimilate, move, or delete source content.

---

## Architecture

```text
KnowledgeAcquisitionDirector
        ↓
AcquisitionProviderRegistry
        ↓
FilesystemAcquisitionProvider
        ↓
AcquisitionPlan
        ↓
Future admission pipeline
        ↓
Frozen assimilation core

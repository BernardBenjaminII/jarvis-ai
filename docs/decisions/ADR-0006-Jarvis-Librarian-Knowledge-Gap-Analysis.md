# ADR-0006: JARVIS Librarian and Knowledge Gap Analysis


> **Legacy ADR**
>
> This ADR was created before the JARVIS ADR governance policy was established.
>
> Duplicate ADR numbers from this era are preserved intentionally for historical continuity.
>
> Beginning with **ADR-0017**, all Architecture Decision Records use unique,
> immutable numbering.

## Status

Accepted

## Date

2026-07-01

## Context

JARVIS is evolving from a simple assistant into a long-lived offline knowledge system. The current knowledge repository already contains structured directories for aviation, computing, emergency preparedness, engineering, geography, mathematics, medical, military, reference, religion, repair, science, and ZIM archives.

The system should not merely ingest whatever files happen to exist on disk. It should understand what knowledge it currently has, evaluate the quality and coverage of that knowledge, identify gaps, and recommend reputable sources to fill those gaps.

A simple downloader would add volume, but not necessarily value. JARVIS needs a collection development subsystem similar to a research librarian: one that catalogs, audits, scores, recommends, stages, and prepares knowledge for ingestion.

## Decision

JARVIS will include a first-class subsystem called the **JARVIS Librarian**.

The Librarian is responsible for:

1. Inventorying the existing knowledge repository.
2. Extracting and maintaining document metadata.
3. Detecting duplicate or near-duplicate documents.
4. Measuring topic coverage across the knowledge taxonomy.
5. Identifying weak, stale, missing, or low-quality subject areas.
6. Searching trusted sources for recommended acquisitions.
7. Downloading approved materials into a staging area.
8. Preparing staged materials for review and later ingestion.
9. Maintaining a catalog database of all known documents and acquisition candidates.

The Librarian will not blindly download everything it finds. It will prefer trusted, reputable, legally accessible sources and place new material into a staging directory before promotion into the main `Knowledge/` tree.

## Goals

The Librarian should answer questions such as:

* What does JARVIS currently know?
* What topics are underrepresented?
* Which areas are stale or outdated?
* Which files are duplicates?
* Which documents are from trusted sources?
* Which documents need OCR?
* Which documents have not yet been embedded?
* Which high-quality sources should be acquired next?

## Non-Goals

The Librarian will not initially:

* Replace the existing knowledge ingestion engine.
* Automatically trust or promote all downloaded material.
* Bypass copyright or licensing restrictions.
* Provide medical, legal, or engineering advice without source attribution.
* Modify the main `Knowledge/` directory without an explicit promotion step.

## Proposed Directory Structure

```text
JARVISDATA/
├── Knowledge/
│   ├── aviation/
│   ├── computing/
│   ├── emergency/
│   ├── engineering/
│   ├── geography/
│   ├── mathematics/
│   ├── medical/
│   ├── military/
│   ├── reference/
│   ├── religion/
│   ├── repair/
│   ├── science/
│   └── zim/
│
└── Jarvis_Downloaded_Knowledge/
    ├── incoming/
    ├── staged/
    ├── rejected/
    ├── approved/
    ├── manifests/
    ├── logs/
    └── sources/
        ├── mit/
        ├── openstax/
        ├── libretexts/
        ├── pubmed/
        ├── nasa/
        ├── faa/
        ├── nist/
        ├── who/
        ├── cdc/
        ├── fema/
        ├── fao/
        ├── us_army/
        ├── usmc/
        └── archive_org/
```

## Core Components

```text
dev/librarian/
├── __init__.py
├── audit.py
├── catalog.py
├── classify.py
├── coverage.py
├── dedupe.py
├── download.py
├── gap_analysis.py
├── inventory.py
├── metadata.py
├── promote.py
├── quality.py
├── sources/
│   ├── base.py
│   ├── mit.py
│   ├── openstax.py
│   ├── libretexts.py
│   ├── pubmed.py
│   ├── nasa.py
│   ├── nist.py
│   ├── who.py
│   ├── cdc.py
│   ├── fema.py
│   └── faa.py
└── README.md
```

## Catalog Database

The Librarian will maintain a SQLite catalog.

Suggested location:

```text
JARVIS_RUNTIME/knowledge/librarian.sqlite
```

Initial tables:

```text
documents
sources
topics
document_topics
acquisition_candidates
audit_runs
coverage_scores
duplicates
ingestion_queue
```

## Document Metadata

Each known document should eventually track:

```yaml
title:
authors:
publisher:
year:
edition:
source_name:
source_url:
license:
file_path:
file_type:
sha256:
size_bytes:
page_count:
language:
topic:
subcategory:
trust_score:
quality_score:
recency_score:
coverage_score:
ocr_required:
embedded:
ingested:
created_at:
updated_at:
```

## Trust Tiers

The Librarian will score sources by trust tier.

### Tier 0: Preferred Sources

Examples:

* MIT OpenCourseWare
* OpenStax
* LibreTexts
* NASA
* NIST
* FAA
* CDC
* WHO
* NIH / PubMed Central
* FEMA
* USGS
* NOAA
* FAO
* official military doctrine repositories

### Tier 1: Good Sources

Examples:

* Wikibooks
* iFixit
* StackExchange ZIM archives
* university course pages
* public-domain technical books

### Tier 2: Review Carefully

Examples:

* blogs
* prepper manuals
* anonymous PDFs
* archive mirrors
* unsourced survival collections

## Knowledge Coverage

The Librarian will compute coverage by taxonomy area.

Example output:

```text
medical/field_medicine        strong
medical/surgery               moderate
medical/radiology             weak
medical/pharmacology          weak
computing/linux               strong
computing/cybersecurity       moderate
computing/distributed_systems missing
engineering/electronics       moderate
engineering/control_systems   missing
mathematics/statistics        missing
science/physics               weak
```

Coverage is based on:

* number of documents
* quality of documents
* source trust
* topic diversity
* recency
* document type
* ingestion status
* embedding status

## Gap Analysis

The Librarian will compare the current collection against a desired knowledge map.

Example:

```yaml
medical:
  anatomy:
    desired_depth: medium
  emergency:
    desired_depth: high
  field_medicine:
    desired_depth: high
  surgery:
    desired_depth: high
  radiology:
    desired_depth: medium
  pharmacology:
    desired_depth: medium
  tropical_medicine:
    desired_depth: medium

computing:
  linux:
    desired_depth: high
  networking:
    desired_depth: high
  cybersecurity:
    desired_depth: high
  operating_systems:
    desired_depth: high
  distributed_systems:
    desired_depth: medium
  compilers:
    desired_depth: medium
```

The result should be a prioritized acquisition list.

## Acquisition Workflow

```text
Audit existing Knowledge/
        ↓
Update catalog.sqlite
        ↓
Compute coverage scores
        ↓
Identify gaps
        ↓
Search trusted sources
        ↓
Create acquisition candidates
        ↓
User review / approval
        ↓
Download to staging
        ↓
Verify checksum and metadata
        ↓
Classify and dedupe
        ↓
Promote to Knowledge/
        ↓
Queue for extraction, chunking, and embedding
```

## CLI Commands

Initial command targets:

```bash
python -m dev.librarian.inventory
python -m dev.librarian.audit
python -m dev.librarian.gap_analysis
python -m dev.librarian.download --source mit --topic calculus
python -m dev.librarian.promote --approved-only
```

Future unified command:

```bash
jarvis librarian audit
jarvis librarian gaps
jarvis librarian recommend
jarvis librarian download --approved
jarvis librarian promote
```

## Staging Rules

New files should not go directly into `Knowledge/`.

They should first go here:

```text
Jarvis_Downloaded_Knowledge/staged/
```

Files that fail validation go here:

```text
Jarvis_Downloaded_Knowledge/rejected/
```

Files approved for knowledge ingestion go here:

```text
Jarvis_Downloaded_Knowledge/approved/
```

Only after review should files be promoted into:

```text
Knowledge/
```

## Consequences

### Positive

* JARVIS gains awareness of its own knowledge coverage.
* Downloads become intentional instead of random.
* Duplicate documents are reduced.
* Weak areas can be systematically improved.
* Source quality becomes measurable.
* Future ingestion and embedding become cleaner.
* The knowledge base becomes auditable and trustworthy.

### Negative

* More initial engineering work.
* Requires a catalog database.
* Requires source-specific crawler maintenance.
* Requires careful handling of licensing and provenance.
* Coverage scoring will be imperfect at first.

## Implementation Plan

### Phase 1: Inventory

Build a scanner that walks `Knowledge/`, records files, hashes, paths, extensions, and basic metadata.

### Phase 2: Catalog

Create `librarian.sqlite` and store all discovered files.

### Phase 3: Dedupe

Detect identical files using SHA-256 and flag duplicate candidates.

### Phase 4: Coverage

Map files to taxonomy categories and produce a simple coverage report.

### Phase 5: Gap Analysis

Compare existing coverage against a desired knowledge map.

### Phase 6: Source Discovery

Implement trusted source crawlers one at a time.

Priority:

1. MIT OCW
2. OpenStax
3. LibreTexts
4. WHO
5. CDC
6. NIST
7. FAA
8. NASA
9. FEMA
10. PubMed Central

### Phase 7: Review Queue

Generate acquisition candidates for user approval.

### Phase 8: Promotion

Move approved, verified, deduplicated files into the main `Knowledge/` tree.

## Final Decision

JARVIS will treat knowledge acquisition as a core capability, not a side script.

The Librarian subsystem will allow JARVIS to understand what it has, what it lacks, what is stale, what is duplicated, and what should be acquired next.

This turns JARVIS from a passive document search assistant into an actively curated offline research library.

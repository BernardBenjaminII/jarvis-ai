# ADR-0009: Knowledge Acquisition Pipeline

## Status

Accepted

## Date

2026-07-02

## Decision

JARVIS will use a knowledge acquisition pipeline with these stages:

1. Acquire source material into staging.
2. Verify downloaded files.
3. Normalize archives and packages.
4. Extract metadata.
5. Filter useful educational assets.
6. Write manifests.
7. Preserve originals.
8. Hand normalized material to the Librarian/catalog later.

## Initial Pilot

MIT OCW course ZIP packages are the pilot format.

The pipeline will preserve original ZIPs while creating clean normalized course folders containing useful files such as PDFs, JSON metadata, text, Markdown, CSV, XML, and selected HTML.

It will ignore web infrastructure such as CSS, JavaScript, fonts, thumbnails, videos, captions, and tracking assets.

## Non-Goals

This ADR does not implement embeddings, RAG, OCR, or automatic promotion into `Knowledge/`.


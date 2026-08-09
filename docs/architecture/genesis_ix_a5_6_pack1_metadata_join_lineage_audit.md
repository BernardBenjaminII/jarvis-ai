# Genesis IX-A5.6 Pack 1 — Metadata Join and Lineage Audit

## Mission

Determine how runtime chunks, source documents, catalog records, index records,
and library records can be joined without modifying the knowledge databases.

## Audit Scope

The pack profiles likely identity and lineage columns, including:

- `id`;
- `document_id`;
- `source_id`;
- `chunk_id`;
- `path`;
- `document_path`;
- `file_path`;
- `source_path`;
- `relative_path`;
- hashes when present.

It scores same-database joins using match coverage and key uniqueness. It also
identifies whether populated category-like metadata can be propagated along each
validated lineage path.

## Decision Classes

- `preferred_join`;
- `usable_with_validation`;
- `weak_join`;
- `reject_join`;
- `inspect_cross_database`;
- `join_error`.

## Safety

Every SQLite database is opened in read-only mode. No records, indexes, schemas,
or source files are changed.

## Next Gate

A5.6 Pack 2 may analyze the category vocabulary only after Pack 1 identifies a
safe lineage from retrieved chunks to metadata-bearing catalog rows.

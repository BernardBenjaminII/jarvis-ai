# Genesis X-A2.2 — Corpus Hygiene & Final Exception Resolution

X-A2.2 closes the materialization campaign by converting ambiguous failures into
explicit terminal states.

Filesystem metadata exclusions:
- `._*` AppleDouble sidecars
- `.DS_Store`
- `Thumbs.db`
- `desktop.ini`

Ordinary dotfiles such as `.gitignore` are preserved.

Already-materialized excluded artifacts are removed transactionally from
`runtime_chunks_fts`, `runtime_chunks`, and `runtime_documents`.

Final legitimate-document recovery reuses X-A2.1. Arabic-language path hints
route OCR through `eng+ara`. Remaining nonrecoverable documents become
`UNRECOVERABLE`, not `FAILED`.

Mutating commands require `--yes`.

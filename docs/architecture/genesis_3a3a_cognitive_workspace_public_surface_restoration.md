# Genesis III-A3A — Cognitive Workspace Public Surface Restoration

## Status

Compatibility repair.

## Purpose

Genesis III-A1 through III-A3 established the cognitive workspace under
`core.cognition.workspace`. Later Genesis VI work narrowed
`core.cognition.__init__` to the executive cognition surface, unintentionally
removing workspace symbols that certified callers imported from
`core.cognition`.

III-A3A restores the package-root workspace exports while preserving every
existing Genesis VI executive cognition export.

## Architectural rule

`core.cognition.workspace` remains the canonical implementation owner.
`core.cognition` provides identity-preserving public re-exports only. No
workspace implementation is duplicated, renamed, or moved.

## Restored compatibility

The repair restores package-root imports including:

- `Assumption`
- `CognitiveWorkspaceService`
- `CognitiveWorkspaceCodec`
- `CognitiveWorkspaceCatalog`
- the complete certified Genesis III workspace public surface

## Non-goals

- No persistence changes
- No schema migrations
- No behavior changes
- No replacement of Genesis VI cognition
- No duplicate cognitive workspace implementation

## Certification

III-A3A requires identity-preserving aliases, a deterministic codec round trip,
and successful Genesis III-A1, III-A2, and III-A3 regressions.

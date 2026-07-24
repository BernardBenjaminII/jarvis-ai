# ADR — Evolutionary Genesis Verification Manifest

**Status:** Accepted  
**Decision scope:** Genesis verification governance  
**Milestone:** Genesis II-A3B

## Context

Genesis II-A3A froze the Genesis verification manifest by asserting exact
equality against a hard-coded list of verifier paths. The rule protected the
certified baseline but also imposed a permanent phase ceiling: adding any valid
future Genesis verifier caused II-A3A to fail.

The verification system must preserve prior certification while allowing
constitutionally ordered growth.

## Decision

Adopt an evolutionary manifest validator with an immutable certified prefix.

The validator shall:

1. preserve the full II-A3A baseline as the exact manifest prefix;
2. parse verifier paths into sortable Genesis phase identities;
3. reject duplicate paths and duplicate phase identities;
4. reject invalid, unsafe, or out-of-order paths;
5. permit later phases only when their identities are strictly increasing;
6. calculate a deterministic fingerprint over the ordered manifest.

II-A3A shall verify baseline preservation rather than exact whole-manifest
equality.

II-A3B shall verify the evolutionary rules and its own registration.

## Consequences

### Positive

- Future Genesis milestones no longer require edits to older constitutional
  verifiers.
- Previously certified suites remain immutable.
- Manifest ordering becomes machine-enforced.
- Duplicate and malformed phase registrations are rejected.
- The manifest has a deterministic identity suitable for later release and
  attestation systems.

### Negative

- Verifier filenames now carry constitutional ordering significance.
- Exceptional verifier names require explicit parser mappings.
- Renaming a certified verifier remains a breaking constitutional change.

## Rejected alternatives

### Continue extending the hard-coded II-A3A list

Rejected because every new milestone would rewrite an older certification
boundary.

### Remove baseline freezing

Rejected because future edits could silently delete or reorder certified suites.

### Sort the manifest automatically

Rejected because automatic sorting could conceal an incorrect human registration
instead of detecting it.

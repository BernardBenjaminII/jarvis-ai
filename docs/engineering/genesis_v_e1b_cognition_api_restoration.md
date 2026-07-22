# Genesis V-E1B — Cognition API Restoration

## Mission

Use the Engineering OS compatibility evidence to restore verified public API
exports in `core.cognition` while refusing to invent an implementation for the
unresolved `CognitiveObject` contract.

## Approved Remediation

Fourteen symbols already implemented in the cognition workspace subsystem are
re-exported through `core.cognition`.

The implementation remains canonical in its existing modules. No duplicate
classes, services, repositories, codecs, enums, or query contracts are created.

## Governed Exception

`core.cognition.common.cognitive_object.CognitiveObject` is not restored
automatically.

The Engineering OS performs repository and Git archaeology, writes evidence to:

- `.artifacts/engineering/cognitive_object_archaeology.json`
- `docs/audits/cognitive_object_archaeology.md`

A Commander decision is required if the evidence does not prove the correct
historical or replacement contract.

## Completion Criterion

The phase is complete when:

1. all fourteen `core.cognition` missing-export findings disappear;
2. the analyzer completes successfully;
3. `CognitiveObject` is represented by no more than one governed finding;
4. V-E1A and earlier Engineering OS regressions pass.

# Genesis IX-A4.8 Pack 2 — Executive Acceptance Harness

## Mission

Provide the permanent executable backbone for JARVIS operational acceptance.

## Runtime Flow

```text
CampaignDefinition
    ↓
AcceptanceRunner
    ↓
RuntimeAdapter
    ↓
Answer + telemetry
    ↓
Assertion evaluation
    ↓
AcceptanceResult
    ↓
Evidence capture
    ↓
Reports and archive
```

## Capabilities

- immutable test-case and result contracts;
- deterministic expectation evaluation;
- primary failure classification;
- response, telemetry, prompt, and trace capture;
- per-run artifact directories;
- JSONL results and failures;
- Markdown and JSON reports;
- live Executive Conversation runtime adapter;
- one-command smoke campaign.

Pack 2 intentionally leaves the full question library, deep live-prompt capture,
Mission Control acceptance page, and readiness-board automation to later packs.

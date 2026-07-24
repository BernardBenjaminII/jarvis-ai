# ADR-0011: Knowledge Discovery Engine

## Status

Accepted

## Date

2026-07-02

## Decision

JARVIS will include a Knowledge Discovery Engine.

The Discovery Engine is responsible for asking:

- What topics does JARVIS want?
- Which trusted sources cover those topics?
- What search plans should be executed?
- Which candidate acquisitions should be reviewed?

Discovery does not download by default. It creates ranked acquisition candidates.

## Initial Scope

The first version will use trusted source profiles and topic plans to generate source-specific research targets.

Supported sources initially:

- MIT OCW
- MIT Press Open Access
- WHO
- CDC
- NIST
- NASA
- FAA
- OpenStax
- LibreTexts
- PubMed Central

## Output

Discovery writes candidate plans to:

```text
/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/discovery/

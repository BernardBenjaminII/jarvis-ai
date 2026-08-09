# Genesis X-B1.2a — Production Context Routing & Campaign Recovery

## Mission

Close the production orchestration gap exposed by the X-B1.2 canary.

All 751 observed terminal failures were canonical chunk context overflows.
X-B1.2a treats context overflow as a routing event, not a terminal failure.

## Recovery

Existing `REJECTED` context-overflow rows are migrated in place:

`REJECTED -> FRAGMENTED -> COMPLETE_FRAGMENTED`

No canonical chunk is rewritten or re-extracted.

## Future routing

Canonical embedding failure is classified.

- context overflow -> first-generation semantic fragments
- fragment overflow -> recursive Revision 2 adaptation
- transient provider failures -> existing retry/isolation path
- other permanent errors remain explicit failures

## Safety

Existing canonical vectors, fragment vectors, bridge rows, and fragment lineage
are preserved.

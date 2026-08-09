# Genesis X-B1.1b Revision 2 — Recursive Context Adaptation

Migration-safe recursive semantic fragmentation. Existing vectors are preserved.
Legacy fragments become depth-0 leaves. Context-rejected leaves are superseded
and replaced by smaller child fragments with parent UUID, depth, path, offsets,
and deterministic identity. Certification evaluates active leaves; historical
SUPERSEDED_CONTEXT ancestors do not count as incomplete work.

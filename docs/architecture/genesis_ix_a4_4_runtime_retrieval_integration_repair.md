# Genesis IX-A4.4 — Runtime Retrieval Integration Repair

## Mission

Repair confirmed ExecutiveDirector integration mismatches using the verified
IX-A4.3C call-graph result.

## Canonical Director Contract

IX-A4.3C resolved the active Director hook as:

```text
submit
```

IX-A4.4 introduces:

```text
core/executive/director_dispatch.py
```

This module resolves the Director callable in the following order:

```text
preferred verified method
submit
dispatch
direct
route
plan
decide
coordinate
handle
process
run
invoke
execute
```

`execute` remains a compatibility fallback only.

## Repair Policy

The installer does not perform unrestricted repository-wide string
replacement.

It:

1. Reads the verified Director hook from IX-A4.3C.
2. Repairs the IX-A4.3B tracer's hard-coded `director.execute`.
3. Uses AST inspection to locate production calls specifically targeting
   `director.execute` or `self.director.execute`.
4. Replaces only confirmed exact call expressions.
5. Compiles repaired files.
6. Reruns IX-A4.3B and IX-A4.3.

## Outputs

```text
docs/audits/genesis_ix_a4_4/
    runtime_integration_repair.json
    runtime_integration_repair.md
```

## Constitutional Rule

No runtime component may assume a Director method name when a verified
call-graph result or canonical resolver is available.

# R3 persistent owned-fixture missions

R3 connects R1's SQLite mission storage and scope helpers to R2's bounded
process runner through a fixed owned-loopback HTTP fixture. This is a lab
workflow, not a vulnerability finder or bounty submission system.

Run from the repository root with the Jarvis Python 3.11 environment:

```
python -m core.bounty_missions demo
python -m core.bounty_missions report MISSION_ID
python -m core.bounty_missions cancel MISSION_ID
```

The database defaults to `$JARVIS_RUNTIME_ROOT/bounty_missions/r3.sqlite`,
or `~/.local/share/jarvis/bounty_missions/r3.sqlite` when unset. An explicit
`--db PATH` must precede the subcommand. Each demo creates a new mission and
consumes one fixture attempt. Report and cancel work across separate processes.
The demo's built-in review applies only to the owned fixture.

Scope accepts synthetic `.test` labels. They are never resolved or used as
network destinations. The subprocess only contacts a temporary server created
by this process on numeric 127.0.0.1, with a random request path. No target,
command line, external URL, scanner, or credential can be supplied through
this CLI. All findings remain `not_a_vulnerability`.

A transaction checks readiness, expiry, policy digest, scope, capability and
remaining budget, marks the task running, and charges one attempt before
subprocess execution. The transaction ends before the subprocess runs, so
another process can cancel the mission. Control checks run through the runner's
cancellation interface. Completion rechecks policy inside its transaction.
Completed tasks return persisted evidence without rerunning. Queued work is
cancelled by the inherited cancel method; an active worker records cancellation
when it observes the change. A process already killed cannot finalize itself.

Attempts remain charged on failure, timeout, cancellation after claim or crash.
A crash leaves the task running with a claim event and no completion evidence.
This means uncertain/interrupted work, not proof of an active process. There is
no automatic recovery, refund or retry. Manual reconciliation is future work.
The CLI does not expose arbitrary task creation or execution; Python callers
can use Store.create/review/queue/run for owned-fixture development.

Controls are cooperative. Cancellation can race with the single fixture request
and cannot undo it. SQLite lock waits and server shutdown affect cancellation
latency. Expiry uses host wall time. Store hashes detect accidental changes;
they are not signatures or a defense against a user who can edit the database.
The process runner controls time, output and process groups; it is not an OS
sandbox. R3 does not gate legacy Jarvis shell, network or recon paths, provide
human identity authentication, or connect to the existing chat/orchestrator.

Installation adds core/bounty_missions, tests/bounty_missions, and this document.
Existing R1/R2 files and runtime databases are not modified. A hash preflight
checks the R1 engine and R2 runner versions used here. Unknown existing R3 files
are refused. Installation runs the ten mission tests and existing worker tests;
on failure it removes newly copied files. The test fixture uses localhost.
No service restart or new dependency installation is required.

Next integration work: expose reviewed mission operations to Jarvis through an
explicit adapter, add program/rules ingestion with source provenance, and design
live adapters with program-specific authorization and network containment.

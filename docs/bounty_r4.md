# R4 opportunity catalog

First connector: HackerOne's documented researcher API, GET /v1/hackers/programs.
Reference checked 2026-09-16: https://api.hackerone.com/hacker-resources/#get-programs
The documented listing supports page[number], page[size] up to 100, and the
program attribute offers_bounties. Authentication is API username/token Basic
Auth over verified HTTPS. Use credentials created for the HackerOne researcher
API, not your website password. Do not paste tokens into chat or Git.

## Install and run

Use ~/.venvs/jarvis-py311/bin/python for each command below, from the Jarvis root.
No new dependencies, service restart or R1-R3 edits are required.

```
python -m core.bounty_catalog demo
python -m core.bounty_catalog discover --max-pages 5
python -m core.bounty_catalog list --paid-only
python -m core.bounty_catalog proposal PROGRAM_HANDLE
```

Discover prompts for the API username and a hidden token. Credentials are kept
in process memory only. Discovery sends GET requests only to api.hackerone.com;
it does not follow redirects, proxy environment variables or policy links. It
does not contact listed programs. There is no report submission or scanner API.
An authenticated live run has not been tested by the package author; tests use
synthetic API responses and mocked transport. Verify your first live run locally.

The default limit is five pages of 100, maximum 20 pages per command. Requests
are spaced by at least one second after processing the prior page. Authentication
errors, rate limits, malformed data and unexpected pagination stop discovery;
there is no automatic retry. A 15-second socket timeout, a checked response-body
deadline and a 2 MiB/page limit constrain responses. These are not a hard
whole-process deadline (system DNS and individual I/O calls can affect timing).

## Catalog and provenance

The default database is $JARVIS_RUNTIME_ROOT/bounty_catalog/r4.sqlite, falling
back to ~/.local/share/jarvis/bounty_catalog/r4.sqlite. `--db PATH` may be placed
before the command. Database file mode is 0600; new parent directories use 0700.
The database can contain private program policies visible to your account.
Keep it local and outside Git; an API listing is not necessarily public data.

Each accepted page stores its raw JSON bytes, SHA-256, source URL and observation
time. Parsed program observations are appended per run. No destructive removal
occurs when a listing disappears. Current views use each program's latest
observation, with seen_in_latest_run and a 24-hour stale indicator. A failed
new run does not turn older observations into freshly verified data. SHA-256 is
a content fingerprint, not a signature or protection against local DB edits.

Run statuses:
- complete: the API returned no next-page link; this is only completion of this
  account's listing, not a claim that every bounty platform/program was found.
- limited: the configured page limit was reached with additional pages present.
- error: discovery stopped; earlier validated pages from that run are retained.
- local_import_unverified: an imported file with unverified provenance.

Duplicate handles within a run abort its database transaction rather than
silently replacing data. If this occurs, rerun discovery; paginated listings may
change during retrieval. A process killed before save commits does not retain
that run. No scheduling, cursor resume or archival retention policy exists yet.

Reward status paid means offers_bounties=true, no_bounty means false, and unknown
means absent/null. False alone does not prove a particular program's purpose.
There is no promised payout, profit score, or invented minimum/maximum reward.
Reward amounts stay null until a verified reward-table integration is added.
source_updated_at stays null if the source supplies no updated_at; last_seen is
our observation time. Listing data does not establish asset eligibility.

Policy text is retained in observations/raw pages but not interpreted as
instructions, rendered as HTML, followed as links, or used to authorize tools.
Proposals contain a review checklist and no executable tasks. Full scope,
exclusions, automation rules, account eligibility and asset-specific rewards
must be collected and reviewed in a later stage. There is no mission, chat,
agent or scheduler integration in this release.

## Offline import

```
python -m core.bounty_catalog import-json /path/to/programs-page.json
python -m core.bounty_catalog list --source hackerone-import --paid-only
python -m core.bounty_catalog proposal HANDLE --source hackerone-import
```

Accepts one HackerOne-format JSON page (up to 2 MiB), not arbitrary HTML. An
import is a local observation; its retrieval time and origin are unverified.
Imported data is separate from live API data. Demo uses a temporary synthetic
catalog, makes no network requests, and never seeds the real opportunity list.

## Verification

Twelve tests cover reward tri-state validation, malformed inputs, fixed-host
pagination, complete/limited/error discovery, changed observations, stale and
missing entries, import separation, non-executable proposals, atomic rollback,
fixed GET transport, authentication errors, rate limiting and redirects.

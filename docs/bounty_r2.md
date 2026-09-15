# Jarvis Bounty R2 — tool identity and local fixture runner

R2 adds `core/bounty_worker`, retains its tests in `tests/bounty_worker`, and
updates only the platform-status route from the supplied snapshot. The route
keeps the original platform/profile result and corrects its HTTPX boolean.

## Install

```bash
cd ~/Projects/jarvis-ai
~/.venvs/jarvis-py311/bin/python ~/Downloads/jarvis_bounty_r2/install.py --project "$PWD"
~/.venvs/jarvis-py311/bin/python -m core.bounty_worker inventory
~/.venvs/jarvis-py311/bin/python -m core.bounty_worker demo
systemctl --user restart jarvis.service
curl --fail --silent --show-error http://127.0.0.1:8000/api/runtime/platform
```

Installation validates checksums and the old route contents, refuses conflicting
files, backs up replaced files, and restores changed files if verification fails.
It never restarts the service automatically. No dependencies are added.

## Implemented and tested

- Static HTTPX identity inspection without running discovered executables.
- Python client identified and excluded from recon capability.
- ELF binary with ProjectDiscovery module marker recognized as a candidate.
  This marker is not cryptographic provenance or a functional readiness check.
- Other tools remain presence-only; no Amass initialization/download is triggered.
- Shell-free process primitive with closed stdin, reduced environment, 5-second
  default timeout, 64 KiB default output cap, cancellation, and POSIX process-group
  cleanup including inherited-pipe timeout handling.
- One real HTTP request to a temporary server bound to 127.0.0.1, using a fixed
  Python client and generated path token. No DNS, proxies or redirects are used.
- CLI exposes only inventory and fixture demo, not arbitrary commands or targets.
- 13 tests, including the route contract with a stubbed original snapshot.

## Limits

This is a local execution-control foundation, not a scanner integration or an
OS sandbox. Generic `run_bounded` is an internal primitive: never expose its argv
parameter to a model, HTTP endpoint or command dispatcher. Descendants that
actively escape their process group require OS isolation; this implementation
is not a containment boundary for hostile code.

R1 database budgets and policy enforcement are NOT integrated into the R2
fixture runner. R1 remains unchanged. No model agents, live program discovery,
live scan adapters, real vulnerability validation or submissions are enabled.
The existing legacy recon entry points and shell-based ping remain unchanged;
they still require hardening before autonomous live execution.

The platform route change affects /api/runtime/platform only. Other code that
calls the underlying snapshot directly may still see its old HTTPX boolean.
A full running Jarvis service was not available in the supplied partial source;
service startup and endpoint response must be checked on Kali after restart.

Static inventory does not install or download tools. Unknown executable wrappers
fail closed. Explicit tool provenance and dedicated service isolation are future
requirements before running scanners automatically.

## Recovery

The installer prints an install_backups directory containing the original route
and a changes.json list. To restore the prior route, copy its
core/src/routes/platform_status.py back to the corresponding project path and
restart the user service. The newly added worker module is inert unless invoked.

## Preserve after verification

```bash
git add -- core/bounty_worker core/src/routes/platform_status.py tests/bounty_worker docs/bounty_r2.md
git diff --cached --check
git commit -m "Add bounded local fixture runner and correct HTTPX identification"
```

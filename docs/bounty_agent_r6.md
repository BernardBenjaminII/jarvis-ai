# JARVIS Bounty Agent R6

R6 adds a bounded autonomous reconnaissance loop above the existing R5/R5.2 authorization and live-mission controls.

The human approves a reviewed R5 authorization first. R6 then lets Jarvis automatically execute only the existing `subfinder` and `httpx` capabilities inside that active authorization.

R6 stops after recon analysis and produces reviewable options. Selecting `pursue` records a human decision only. It does not execute deeper testing.

Human approval remains required before deeper target-specific investigation, vulnerability validation, and report submission.

Safety invariants:
- Live agent sessions start only on detected Kali.
- Existing unexpired, unrevoked R5 authorization is mandatory.
- Root target must pass `scope.require(..., "subfinder")`.
- Every HTTPX candidate is created through the R5.2 proposal path.
- R5 approval rechecks current authorization before creating the HTTPX task.
- R5 run rechecks authorization and scope before execution and again at commit time.
- R6 does not add Nuclei, fuzzing, port scanning, exploitation, credential attacks, report submission or arbitrary command execution.

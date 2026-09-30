# Jarvis Bounty R5.2 — reviewed discovery fan-out

R5.2 adds a proposal layer between passive subdomain discovery and HTTP
probing.

A completed R5.1 subfinder task may generate HTTPX proposals from its
already scope-filtered accepted hosts. Proposal generation performs no
network activity.

Every proposed hostname is revalidated against the current reviewed
authorization. Proposals are persisted with parent-task provenance,
authorization/scope digest evidence and a SHA-256 fingerprint.

A proposal must be explicitly approved before a normal queued HTTPX task
is created. Approval rechecks the authorization and scope. Approval does
not execute the HTTPX task.

Rejected proposals never become tasks.

R5.2 does not add:
- arbitrary command execution;
- automatic HTTPX fan-out;
- vulnerability scanning;
- Nuclei;
- fuzzing;
- port scanning;
- automatic policy interpretation;
- model/chat execution authority.

CLI:

    python -m core.bounty_live propose-httpx SUBFINDER_TASK_ID
    python -m core.bounty_live proposals MISSION_ID
    python -m core.bounty_live approve PROPOSAL_ID --reviewer NAME
    python -m core.bounty_live reject PROPOSAL_ID --reviewer NAME

Approved tasks are executed separately using the existing R5.1 `run`
command.

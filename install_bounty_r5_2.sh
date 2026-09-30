#!/usr/bin/env bash
set -euo pipefail

echo "================================================================"
echo " JARVIS BOUNTY R5.2 — REVIEWED DISCOVERY FAN-OUT"
echo "================================================================"

mkdir -p tests/bounty_live

python3 - <<'PY'
from pathlib import Path

p = Path("core/bounty_live/engine.py")
s = p.read_text()

old = '''            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission TEXT NOT NULL,
                at REAL NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT
            );
'''

new = '''            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                mission TEXT NOT NULL,
                parent_task TEXT NOT NULL,
                capability TEXT NOT NULL,
                target TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                reviewed REAL,
                reviewer TEXT,
                evidence TEXT NOT NULL,
                evidence_sha256 TEXT NOT NULL,
                UNIQUE(mission,capability,target),
                FOREIGN KEY(mission) REFERENCES missions(id),
                FOREIGN KEY(parent_task) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission TEXT NOT NULL,
                at REAL NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT
            );
'''

if old not in s:
    raise SystemExit("Schema anchor not found")

s = s.replace(old, new)

anchor = '''    def report(self, mission):
'''

addition = r'''    def propose_httpx_from_subfinder(self, task_id):
        """Create reviewable HTTPX proposals from completed subfinder evidence.

        No network execution occurs here.
        """
        with self.db() as db:
            task = db.execute(
                "SELECT * FROM tasks WHERE id=?",
                (task_id,),
            ).fetchone()

            if not task:
                raise ValueError("Unknown parent task")

            if task["capability"] != "subfinder":
                raise ValueError("Parent task must be subfinder")

            if task["state"] != "completed" or not task["evidence"]:
                raise ValueError("Parent subfinder task is not completed")

            mission = db.execute(
                "SELECT * FROM missions WHERE id=?",
                (task["mission"],),
            ).fetchone()

            if not mission or mission["state"] != "ready":
                raise ValueError("Mission is not ready")

            scope = self.authorization_store.live_scope(
                mission["authorization"]
            )

            evidence = json.loads(task["evidence"])

            discovered = (
                evidence.get("result", {}).get("accepted", [])
            )

            proposals = []

            for candidate in discovered:
                # Authorization is rechecked before a proposal exists.
                target = scope.require(candidate, "httpx")

                record = {
                    "schema": "jarvis-bounty-proposal-r5.2",
                    "mission_id": mission["id"],
                    "parent_task": task_id,
                    "capability": "httpx",
                    "target": target,
                    "authorization_id": mission["authorization"],
                    "scope_sha256": scope.evidence()["scope_sha256"],
                    "created_at": time.time(),
                }

                raw = json.dumps(
                    record,
                    sort_keys=True,
                    separators=(",", ":"),
                )

                digest = hashlib.sha256(
                    raw.encode()
                ).hexdigest()

                pid = str(uuid.uuid4())

                try:
                    db.execute(
                        """
                        INSERT INTO proposals(
                            id,mission,parent_task,capability,target,
                            state,created,evidence,evidence_sha256
                        ) VALUES(?,?,?,?,?,'proposed',?,?,?)
                        """,
                        (
                            pid,
                            mission["id"],
                            task_id,
                            "httpx",
                            target,
                            time.time(),
                            raw,
                            digest,
                        ),
                    )

                    self._event(
                        db,
                        mission["id"],
                        "proposed",
                        f"httpx:{target} from {task_id}",
                    )

                except sqlite3.IntegrityError:
                    row = db.execute(
                        """
                        SELECT id FROM proposals
                        WHERE mission=? AND capability=? AND target=?
                        """,
                        (
                            mission["id"],
                            "httpx",
                            target,
                        ),
                    ).fetchone()

                    pid = row["id"]

                proposals.append(pid)

        return proposals

    def proposals(self, mission, state=None):
        with self.db() as db:
            if state is None:
                rows = db.execute(
                    """
                    SELECT * FROM proposals
                    WHERE mission=?
                    ORDER BY created,target
                    """,
                    (mission,),
                ).fetchall()
            else:
                rows = db.execute(
                    """
                    SELECT * FROM proposals
                    WHERE mission=? AND state=?
                    ORDER BY created,target
                    """,
                    (mission, state),
                ).fetchall()

        result = []

        for row in rows:
            item = dict(row)

            if item["evidence"]:
                item["evidence"] = json.loads(
                    item["evidence"]
                )

            result.append(item)

        return result

    def approve_proposal(self, proposal_id, reviewer):
        """Approve one proposal and create its normal queued task.

        Approval does not execute the task.
        """
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("Reviewer identity required")

        with self.db() as db:
            proposal = db.execute(
                "SELECT * FROM proposals WHERE id=?",
                (proposal_id,),
            ).fetchone()

            if not proposal:
                raise ValueError("Unknown proposal")

            if proposal["state"] == "approved":
                existing = db.execute(
                    """
                    SELECT id FROM tasks
                    WHERE mission=? AND capability=? AND target=?
                    """,
                    (
                        proposal["mission"],
                        proposal["capability"],
                        proposal["target"],
                    ),
                ).fetchone()

                if existing:
                    return existing["id"]

                raise ValueError(
                    "Approved proposal has no corresponding task"
                )

            if proposal["state"] != "proposed":
                raise ValueError("Proposal is not reviewable")

            mission = db.execute(
                "SELECT * FROM missions WHERE id=?",
                (proposal["mission"],),
            ).fetchone()

            if not mission or mission["state"] != "ready":
                raise ValueError("Mission is not ready")

            # Authorization and scope are rechecked at approval time.
            scope = self.authorization_store.live_scope(
                mission["authorization"]
            )

            target = scope.require(
                proposal["target"],
                proposal["capability"],
            )

            raw = proposal["evidence"]

            if hashlib.sha256(raw.encode()).hexdigest() != \
                    proposal["evidence_sha256"]:
                raise ValueError("Proposal evidence digest mismatch")

            task_id = str(uuid.uuid4())

            try:
                db.execute(
                    """
                    INSERT INTO tasks(
                        id,mission,capability,target,state,created
                    ) VALUES(?,?,?,?,?,?)
                    """,
                    (
                        task_id,
                        mission["id"],
                        proposal["capability"],
                        target,
                        "queued",
                        time.time(),
                    ),
                )

            except sqlite3.IntegrityError:
                existing = db.execute(
                    """
                    SELECT id FROM tasks
                    WHERE mission=? AND capability=? AND target=?
                    """,
                    (
                        mission["id"],
                        proposal["capability"],
                        target,
                    ),
                ).fetchone()

                task_id = existing["id"]

            db.execute(
                """
                UPDATE proposals
                SET state='approved',reviewed=?,reviewer=?
                WHERE id=?
                """,
                (
                    time.time(),
                    reviewer.strip(),
                    proposal_id,
                ),
            )

            self._event(
                db,
                mission["id"],
                "proposal_approved",
                f"{proposal_id}:{reviewer.strip()}",
            )

        return task_id

    def reject_proposal(self, proposal_id, reviewer):
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("Reviewer identity required")

        with self.db() as db:
            proposal = db.execute(
                "SELECT * FROM proposals WHERE id=?",
                (proposal_id,),
            ).fetchone()

            if not proposal:
                raise ValueError("Unknown proposal")

            if proposal["state"] != "proposed":
                raise ValueError("Proposal is not reviewable")

            db.execute(
                """
                UPDATE proposals
                SET state='rejected',reviewed=?,reviewer=?
                WHERE id=?
                """,
                (
                    time.time(),
                    reviewer.strip(),
                    proposal_id,
                ),
            )

            self._event(
                db,
                proposal["mission"],
                "proposal_rejected",
                f"{proposal_id}:{reviewer.strip()}",
            )

'''

if anchor not in s:
    raise SystemExit("report() anchor not found")

s = s.replace(anchor, addition + anchor)

# Include proposals in report output.
old_report = '''        return {
            "mission": dict(m),
            "tasks": tasks,
            "events": events,
        }
'''

new_report = '''        return {
            "mission": dict(m),
            "tasks": tasks,
            "proposals": self.proposals(mission),
            "events": events,
        }
'''

if old_report not in s:
    raise SystemExit("Report return anchor not found")

s = s.replace(old_report, new_report)

p.write_text(s)
print("Patched", p)
PY

python3 - <<'PY'
from pathlib import Path

p = Path("core/bounty_live/__main__.py")
s = p.read_text()

old = '''    rep = sub.add_parser("report")
    rep.add_argument("mission")

    args = p.parse_args()
'''

new = '''    rep = sub.add_parser("report")
    rep.add_argument("mission")

    prop = sub.add_parser("propose-httpx")
    prop.add_argument("task")

    lp = sub.add_parser("proposals")
    lp.add_argument("mission")
    lp.add_argument(
        "--state",
        choices=["proposed", "approved", "rejected"],
    )

    ap = sub.add_parser("approve")
    ap.add_argument("proposal")
    ap.add_argument("--reviewer", required=True)

    rp = sub.add_parser("reject")
    rp.add_argument("proposal")
    rp.add_argument("--reviewer", required=True)

    args = p.parse_args()
'''

if old not in s:
    raise SystemExit("CLI parser anchor not found")

s = s.replace(old, new)

old = '''    elif args.command == "report":
        out = store.report(args.mission)

    print(json.dumps(out, indent=2, sort_keys=True))
'''

new = '''    elif args.command == "report":
        out = store.report(args.mission)

    elif args.command == "propose-httpx":
        out = {
            "proposal_ids":
                store.propose_httpx_from_subfinder(args.task)
        }

    elif args.command == "proposals":
        out = {
            "proposals":
                store.proposals(args.mission, args.state)
        }

    elif args.command == "approve":
        out = {
            "task_id": store.approve_proposal(
                args.proposal,
                args.reviewer,
            )
        }

    elif args.command == "reject":
        store.reject_proposal(
            args.proposal,
            args.reviewer,
        )
        out = {"state": "rejected"}

    print(json.dumps(out, indent=2, sort_keys=True))
'''

if old not in s:
    raise SystemExit("CLI dispatch anchor not found")

p.write_text(s.replace(old, new))
print("Patched", p)
PY

cat > tests/bounty_live/test_proposals.py <<'PY'
import json

import pytest

from core.bounty_authorization import AuthorizationStore
from core.bounty_live.engine import LiveMissionStore


def environment(tmp_path):
    auths = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = auths.create(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        capabilities=["subfinder", "httpx"],
        reviewer="scope-reviewer",
        source_material="reviewed synthetic rules",
        ttl=3600,
    )

    store = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auths,
    )

    mission = store.create(auth, budget=10)

    parent = store.queue(
        mission,
        "subfinder",
        "example.com",
    )

    evidence = {
        "schema": "jarvis-bounty-live-r5.1",
        "mission_id": mission,
        "task_id": parent,
        "authorization_id": auth,
        "program": "demo",
        "capability": "subfinder",
        "target": "example.com",
        "tool": {
            "binary_path": "/test/subfinder",
            "tool_version": "test",
        },
        "result": {
            "adapter": "subfinder",
            "target": "example.com",
            "state": "completed",
            "returncode": 0,
            "accepted": [
                "a.example.com",
                "b.example.com",
            ],
            "rejected": [],
        },
        "recorded_at": 1.0,
    }

    raw = json.dumps(
        evidence,
        sort_keys=True,
        separators=(",", ":"),
    )

    import hashlib

    with store.db() as db:
        db.execute(
            """
            UPDATE tasks
            SET state='completed',
                evidence=?,
                evidence_sha256=?,
                finished=?
            WHERE id=?
            """,
            (
                raw,
                hashlib.sha256(raw.encode()).hexdigest(),
                1.0,
                parent,
            ),
        )

    return auths, auth, store, mission, parent


def test_proposal_generation_is_non_executing(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    ids = store.propose_httpx_from_subfinder(parent)

    assert len(ids) == 2

    proposals = store.proposals(mission)

    assert [x["target"] for x in proposals] == [
        "a.example.com",
        "b.example.com",
    ]

    with store.db() as db:
        httpx_tasks = db.execute(
            """
            SELECT COUNT(*) AS n
            FROM tasks
            WHERE mission=? AND capability='httpx'
            """,
            (mission,),
        ).fetchone()["n"]

    assert httpx_tasks == 0


def test_approval_creates_queued_task(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    pid = store.propose_httpx_from_subfinder(parent)[0]

    tid = store.approve_proposal(
        pid,
        "human-reviewer",
    )

    report = store.report(mission)

    task = [
        x for x in report["tasks"]
        if x["id"] == tid
    ][0]

    assert task["capability"] == "httpx"
    assert task["state"] == "queued"

    proposal = [
        x for x in report["proposals"]
        if x["id"] == pid
    ][0]

    assert proposal["state"] == "approved"
    assert proposal["reviewer"] == "human-reviewer"


def test_reject_does_not_create_task(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    pid = store.propose_httpx_from_subfinder(parent)[0]

    store.reject_proposal(
        pid,
        "human-reviewer",
    )

    proposal = [
        x for x in store.proposals(mission)
        if x["id"] == pid
    ][0]

    assert proposal["state"] == "rejected"

    with store.db() as db:
        count = db.execute(
            """
            SELECT COUNT(*) AS n
            FROM tasks
            WHERE mission=? AND capability='httpx'
            """,
            (mission,),
        ).fetchone()["n"]

    assert count == 0


def test_proposals_are_deduplicated(tmp_path):
    _, _, store, mission, parent = environment(tmp_path)

    first = store.propose_httpx_from_subfinder(parent)
    second = store.propose_httpx_from_subfinder(parent)

    assert first == second
    assert len(store.proposals(mission)) == 2


def test_proposal_requires_completed_subfinder(tmp_path):
    _, auth, store, mission, parent = environment(tmp_path)

    other = store.queue(
        mission,
        "httpx",
        "a.example.com",
    )

    with pytest.raises(ValueError):
        store.propose_httpx_from_subfinder(other)


def test_scope_rechecked_at_approval(tmp_path):
    auths, auth, store, mission, parent = environment(tmp_path)

    pid = store.propose_httpx_from_subfinder(parent)[0]

    auths.revoke(auth, "rules changed")

    with pytest.raises(Exception):
        store.approve_proposal(
            pid,
            "human-reviewer",
        )
PY

cat > docs/bounty_r5_2.md <<'MD'
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
MD

echo
echo "=== R5.2 TESTS =================================================="

python3 -m pytest \
  tests/bounty_live \
  tests/bounty_authorization \
  tests/bounty_scope \
  tests/bounty_adapters \
  tests/bounty_catalog \
  tests/bounty_credentials \
  tests/bounty_missions \
  tests/bounty_worker \
  -q

echo
echo "=== COMPILE ====================================================="

python3 -m compileall -q core/bounty_live

echo
echo "=== DIFF CHECK =================================================="

git diff --check

echo
echo "=== CLI ========================================================="

python3 -m core.bounty_live --help

echo
echo "=== STATUS ======================================================"

git status --short

echo
echo "================================================================"
echo " R5.2 INSTALLATION COMPLETE"
echo "================================================================"

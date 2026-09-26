#!/usr/bin/env bash
set -euo pipefail

echo "================================================================"
echo " JARVIS BOUNTY R5.1 — AUTHORIZATION + LIVE MISSION PERSISTENCE"
echo "================================================================"

mkdir -p \
  core/bounty_authorization \
  core/bounty_live \
  tests/bounty_authorization \
  tests/bounty_live

cat > core/bounty_authorization/__init__.py <<'PY'
from .store import AuthorizationStore, AuthorizationDenied

__all__ = ["AuthorizationStore", "AuthorizationDenied"]
PY

cat > core/bounty_authorization/store.py <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

from core.bounty_scope import LiveScope, ScopeDenied


class AuthorizationDenied(ValueError):
    pass


def _default_db():
    root = os.environ.get("JARVIS_RUNTIME_ROOT")

    if root:
        return Path(root) / "bounty_authorization" / "r5_1.sqlite"

    return Path.home() / ".local/share/jarvis/bounty_authorization/r5_1.sqlite"


class AuthorizationStore:
    def __init__(self, path=None):
        self.path = Path(path or _default_db()).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._init()

        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def _init(self):
        with self.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS authorizations (
                id TEXT PRIMARY KEY,
                program TEXT NOT NULL,
                scope_json TEXT NOT NULL,
                scope_sha256 TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                reviewed_at REAL NOT NULL,
                expires REAL NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                note TEXT
            );

            CREATE INDEX IF NOT EXISTS auth_program_idx
                ON authorizations(program);

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                authorization TEXT NOT NULL,
                at REAL NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT,
                FOREIGN KEY(authorization) REFERENCES authorizations(id)
            );
            """)

    def _event(self, db, auth_id, kind, detail=""):
        db.execute(
            "INSERT INTO events(authorization,at,kind,detail) VALUES(?,?,?,?)",
            (auth_id, time.time(), kind, detail),
        )

    def create(
        self,
        *,
        program,
        include,
        exclude=(),
        capabilities=("subfinder", "httpx"),
        reviewer,
        source_material,
        ttl=86400,
        note="",
    ):
        if type(ttl) is not int or not 60 <= ttl <= 2592000:
            raise AuthorizationDenied("TTL must be between 60 seconds and 30 days")

        scope = LiveScope.reviewed(
            program=program,
            include=include,
            exclude=exclude,
            allowed_capabilities=capabilities,
            reviewed_by=reviewer,
            source_material=source_material,
        )

        evidence = scope.evidence()

        auth_id = str(uuid.uuid4())

        scope_json = json.dumps(evidence, sort_keys=True)

        expires = time.time() + ttl

        with self.db() as db:
            db.execute(
                """
                INSERT INTO authorizations(
                    id,program,scope_json,scope_sha256,source_sha256,
                    reviewer,reviewed_at,expires,revoked,note
                ) VALUES(?,?,?,?,?,?,?,?,0,?)
                """,
                (
                    auth_id,
                    scope.program,
                    scope_json,
                    evidence["scope_sha256"],
                    evidence["source_digest"],
                    scope.reviewed_by,
                    scope.reviewed_at,
                    expires,
                    note,
                ),
            )

            self._event(db, auth_id, "created", "Reviewed live authorization created")

        return auth_id

    def revoke(self, auth_id, reason=""):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM authorizations WHERE id=?",
                (auth_id,),
            ).fetchone()

            if not row:
                raise AuthorizationDenied("Unknown authorization")

            db.execute(
                "UPDATE authorizations SET revoked=1 WHERE id=?",
                (auth_id,),
            )

            self._event(db, auth_id, "revoked", reason)

    def get(self, auth_id):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM authorizations WHERE id=?",
                (auth_id,),
            ).fetchone()

        if not row:
            raise AuthorizationDenied("Unknown authorization")

        return dict(row)

    def live_scope(self, auth_id):
        row = self.get(auth_id)

        if row["revoked"]:
            raise AuthorizationDenied("Authorization revoked")

        if time.time() >= row["expires"]:
            raise AuthorizationDenied("Authorization expired")

        try:
            raw = json.loads(row["scope_json"])
        except json.JSONDecodeError as exc:
            raise AuthorizationDenied("Authorization record corrupted") from exc

        check = hashlib.sha256(
            json.dumps(raw, sort_keys=True).encode()
        ).hexdigest()

        if check != row["scope_sha256"]:
            raise AuthorizationDenied("Scope digest mismatch")

        scope = LiveScope(
            program=raw["program"],
            include=tuple(raw["include"]),
            exclude=tuple(raw["exclude"]),
            allowed_capabilities=tuple(raw["allowed_capabilities"]),
            reviewed_by=raw["reviewed_by"],
            source_digest=raw["source_digest"],
            reviewed_at=raw["reviewed_at"],
        )

        return scope

    def events(self, auth_id):
        with self.db() as db:
            return [
                dict(x)
                for x in db.execute(
                    "SELECT * FROM events WHERE authorization=? ORDER BY id",
                    (auth_id,),
                ).fetchall()
            ]
PY

cat > core/bounty_live/__init__.py <<'PY'
from .engine import LiveMissionStore

__all__ = ["LiveMissionStore"]
PY

cat > core/bounty_live/engine.py <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path

from core.bounty_adapters import enumerate_subdomains, probe_http
from core.bounty_authorization import AuthorizationStore, AuthorizationDenied


def _default_db():
    root = os.environ.get("JARVIS_RUNTIME_ROOT")

    if root:
        return Path(root) / "bounty_live" / "r5_1.sqlite"

    return Path.home() / ".local/share/jarvis/bounty_live/r5_1.sqlite"


class LiveMissionStore:
    def __init__(self, path=None, authorization_store=None):
        self.path = Path(path or _default_db()).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        self.authorization_store = authorization_store or AuthorizationStore()

        self._init()

        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def _init(self):
        with self.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY,
                authorization TEXT NOT NULL,
                program TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                budget INTEGER NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                mission TEXT NOT NULL,
                capability TEXT NOT NULL,
                target TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                started REAL,
                finished REAL,
                evidence TEXT,
                evidence_sha256 TEXT,
                FOREIGN KEY(mission) REFERENCES missions(id)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS task_unique
                ON tasks(mission,capability,target);

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission TEXT NOT NULL,
                at REAL NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT
            );
            """)

    def _event(self, db, mission, kind, detail=""):
        db.execute(
            "INSERT INTO events(mission,at,kind,detail) VALUES(?,?,?,?)",
            (mission, time.time(), kind, detail),
        )

    def create(self, authorization, *, budget=100):
        if type(budget) is not int or not 1 <= budget <= 1000:
            raise ValueError("Budget must be 1..1000")

        scope = self.authorization_store.live_scope(authorization)

        mission = str(uuid.uuid4())

        with self.db() as db:
            db.execute(
                """
                INSERT INTO missions(id,authorization,program,state,created,budget,used)
                VALUES(?,?,?,?,?,?,0)
                """,
                (
                    mission,
                    authorization,
                    scope.program,
                    "ready",
                    time.time(),
                    budget,
                ),
            )

            self._event(
                db,
                mission,
                "created",
                f"Authorization {authorization}",
            )

        return mission

    def queue(self, mission, capability, target):
        with self.db() as db:
            m = db.execute(
                "SELECT * FROM missions WHERE id=?",
                (mission,),
            ).fetchone()

            if not m:
                raise ValueError("Unknown mission")

            if m["state"] != "ready":
                raise ValueError("Mission is not ready")

            scope = self.authorization_store.live_scope(
                m["authorization"]
            )

            target = scope.require(target, capability)

            task = str(uuid.uuid4())

            try:
                db.execute(
                    """
                    INSERT INTO tasks(
                        id,mission,capability,target,state,created
                    ) VALUES(?,?,?,?,?,?)
                    """,
                    (
                        task,
                        mission,
                        capability,
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
                    (mission, capability, target),
                ).fetchone()

                return existing["id"]

            self._event(
                db,
                mission,
                "queued",
                f"{capability}:{target}",
            )

        return task

    def _tool_metadata(self, capability):
        path = shutil.which(capability)

        if not path:
            return {
                "binary_path": None,
                "tool_version": None,
            }

        real = os.path.realpath(path)

        version = None

        commands = [
            [real, "-version"],
            [real, "--version"],
            [real, "-V"],
        ]

        for argv in commands:
            try:
                p = subprocess.run(
                    argv,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=2,
                    shell=False,
                )
            except Exception:
                continue

            text = (p.stdout or "").strip()

            if text:
                version = text.splitlines()[0][:300]
                break

        return {
            "binary_path": real,
            "tool_version": version,
        }

    def run(self, task_id, *, cancel=None):
        with self.db() as db:
            task = db.execute(
                "SELECT * FROM tasks WHERE id=?",
                (task_id,),
            ).fetchone()

            if not task:
                raise ValueError("Unknown task")

            mission = db.execute(
                "SELECT * FROM missions WHERE id=?",
                (task["mission"],),
            ).fetchone()

            if not mission:
                raise ValueError("Missing mission")

            if task["state"] == "completed":
                return json.loads(task["evidence"])

            if task["state"] != "queued":
                raise ValueError("Task is not queued")

            if mission["state"] != "ready":
                raise ValueError("Mission is not ready")

            if mission["used"] >= mission["budget"]:
                raise ValueError("Mission budget exhausted")

            scope = self.authorization_store.live_scope(
                mission["authorization"]
            )

            scope.require(
                task["target"],
                task["capability"],
            )

            db.execute(
                """
                UPDATE tasks
                SET state='running', started=?
                WHERE id=?
                """,
                (time.time(), task_id),
            )

            db.execute(
                "UPDATE missions SET used=used+1 WHERE id=?",
                (mission["id"],),
            )

            self._event(
                db,
                mission["id"],
                "claimed",
                task_id,
            )

        capability = task["capability"]
        target = task["target"]

        tool = self._tool_metadata(capability)

        if capability == "subfinder":
            result = enumerate_subdomains(
                scope,
                target,
                cancel=cancel,
            )
        elif capability == "httpx":
            result = probe_http(
                scope,
                target,
                cancel=cancel,
            )
        else:
            raise ValueError("Unsupported live capability")

        evidence = {
            "schema": "jarvis-bounty-live-r5.1",
            "mission_id": mission["id"],
            "task_id": task_id,
            "authorization_id": mission["authorization"],
            "program": mission["program"],
            "capability": capability,
            "target": target,
            "tool": tool,
            "result": result,
            "recorded_at": time.time(),
        }

        raw = json.dumps(
            evidence,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = hashlib.sha256(
            raw.encode()
        ).hexdigest()

        state = (
            "completed"
            if result.get("state") == "completed"
            and result.get("returncode") == 0
            else "failed"
        )

        with self.db() as db:
            current_mission = db.execute(
                "SELECT * FROM missions WHERE id=?",
                (mission["id"],),
            ).fetchone()

            # Authorization must still be valid at commit time.
            self.authorization_store.live_scope(
                current_mission["authorization"]
            )

            db.execute(
                """
                UPDATE tasks
                SET state=?, finished=?, evidence=?, evidence_sha256=?
                WHERE id=?
                """,
                (
                    state,
                    time.time(),
                    raw,
                    digest,
                    task_id,
                ),
            )

            self._event(
                db,
                mission["id"],
                "completed" if state == "completed" else "failed",
                task_id,
            )

        return evidence

    def report(self, mission):
        with self.db() as db:
            m = db.execute(
                "SELECT * FROM missions WHERE id=?",
                (mission,),
            ).fetchone()

            if not m:
                raise ValueError("Unknown mission")

            tasks = [
                dict(x)
                for x in db.execute(
                    "SELECT * FROM tasks WHERE mission=? ORDER BY created",
                    (mission,),
                ).fetchall()
            ]

            events = [
                dict(x)
                for x in db.execute(
                    "SELECT * FROM events WHERE mission=? ORDER BY id",
                    (mission,),
                ).fetchall()
            ]

        for task in tasks:
            if task["evidence"]:
                task["evidence"] = json.loads(task["evidence"])

        return {
            "mission": dict(m),
            "tasks": tasks,
            "events": events,
        }
PY

cat > core/bounty_live/__main__.py <<'PY'
import argparse
import json

from core.bounty_authorization import AuthorizationStore
from .engine import LiveMissionStore


def main():
    p = argparse.ArgumentParser(
        description="Jarvis bounty R5.1 reviewed live mission engine"
    )

    p.add_argument("--db")

    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create")
    c.add_argument("authorization")
    c.add_argument("--budget", type=int, default=100)

    q = sub.add_parser("queue")
    q.add_argument("mission")
    q.add_argument("capability", choices=["subfinder", "httpx"])
    q.add_argument("target")

    r = sub.add_parser("run")
    r.add_argument("task")

    rep = sub.add_parser("report")
    rep.add_argument("mission")

    args = p.parse_args()

    store = LiveMissionStore(path=args.db)

    if args.command == "create":
        out = {
            "mission_id": store.create(
                args.authorization,
                budget=args.budget,
            )
        }

    elif args.command == "queue":
        out = {
            "task_id": store.queue(
                args.mission,
                args.capability,
                args.target,
            )
        }

    elif args.command == "run":
        out = store.run(args.task)

    elif args.command == "report":
        out = store.report(args.mission)

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
PY

cat > core/bounty_authorization/__main__.py <<'PY'
import argparse
import json
from pathlib import Path

from .store import AuthorizationStore


def main():
    p = argparse.ArgumentParser(
        description="Jarvis bounty R5.1 reviewed authorization store"
    )

    p.add_argument("--db")

    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create")
    c.add_argument("program")
    c.add_argument("--include", action="append", required=True)
    c.add_argument("--exclude", action="append", default=[])
    c.add_argument(
        "--capability",
        action="append",
        choices=["subfinder", "httpx"],
        default=[],
    )
    c.add_argument("--reviewer", required=True)
    c.add_argument("--source-file", required=True)
    c.add_argument("--ttl", type=int, default=86400)
    c.add_argument("--note", default="")

    g = sub.add_parser("show")
    g.add_argument("authorization")

    r = sub.add_parser("revoke")
    r.add_argument("authorization")
    r.add_argument("--reason", default="")

    args = p.parse_args()

    store = AuthorizationStore(path=args.db)

    if args.command == "create":
        source = Path(args.source_file).read_text(
            encoding="utf-8"
        )

        capabilities = (
            args.capability
            if args.capability
            else ["subfinder", "httpx"]
        )

        auth = store.create(
            program=args.program,
            include=args.include,
            exclude=args.exclude,
            capabilities=capabilities,
            reviewer=args.reviewer,
            source_material=source,
            ttl=args.ttl,
            note=args.note,
        )

        out = {
            "authorization_id": auth,
            "record": store.get(auth),
        }

    elif args.command == "show":
        out = {
            "record": store.get(args.authorization),
            "events": store.events(args.authorization),
        }

    elif args.command == "revoke":
        store.revoke(
            args.authorization,
            reason=args.reason,
        )
        out = {"state": "revoked"}

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
PY

cat > tests/bounty_authorization/test_authorization.py <<'PY'
import time
import pytest

from core.bounty_authorization import AuthorizationStore, AuthorizationDenied


def test_authorization_round_trip(tmp_path):
    store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = store.create(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        capabilities=["subfinder", "httpx"],
        reviewer="tester",
        source_material="reviewed rules",
        ttl=3600,
    )

    scope = store.live_scope(auth)

    assert scope.program == "demo"
    assert scope.require("a.example.com", "httpx") == "a.example.com"


def test_revocation_blocks_use(tmp_path):
    store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = store.create(
        program="demo",
        include=["example.com"],
        reviewer="tester",
        source_material="reviewed rules",
        ttl=3600,
    )

    store.revoke(auth, "test")

    with pytest.raises(AuthorizationDenied):
        store.live_scope(auth)
PY

cat > tests/bounty_live/test_live.py <<'PY'
from core.bounty_authorization import AuthorizationStore
from core.bounty_live.engine import LiveMissionStore
import core.bounty_live.engine as engine


def setup(tmp_path):
    auth_store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = auth_store.create(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        reviewer="tester",
        source_material="reviewed rules",
        ttl=3600,
    )

    missions = LiveMissionStore(
        tmp_path / "live.sqlite",
        authorization_store=auth_store,
    )

    return auth_store, auth, missions


def test_create_and_queue(tmp_path):
    _, auth, missions = setup(tmp_path)

    mid = missions.create(auth, budget=5)

    tid = missions.queue(
        mid,
        "subfinder",
        "example.com",
    )

    report = missions.report(mid)

    assert report["mission"]["budget"] == 5
    assert report["tasks"][0]["id"] == tid


def test_live_subfinder_persists_evidence(tmp_path, monkeypatch):
    _, auth, missions = setup(tmp_path)

    mid = missions.create(auth, budget=5)

    tid = missions.queue(
        mid,
        "subfinder",
        "example.com",
    )

    monkeypatch.setattr(
        engine,
        "enumerate_subdomains",
        lambda scope, target, cancel=None: {
            "adapter": "subfinder",
            "target": target,
            "state": "completed",
            "returncode": 0,
            "accepted": ["a.example.com"],
            "rejected": [],
        },
    )

    monkeypatch.setattr(
        missions,
        "_tool_metadata",
        lambda capability: {
            "binary_path": "/test/subfinder",
            "tool_version": "test-version",
        },
    )

    result = missions.run(tid)

    assert result["schema"] == "jarvis-bounty-live-r5.1"
    assert result["result"]["accepted"] == ["a.example.com"]

    report = missions.report(mid)

    assert report["tasks"][0]["state"] == "completed"
    assert report["tasks"][0]["evidence_sha256"]


def test_budget_enforced(tmp_path):
    _, auth, missions = setup(tmp_path)

    mid = missions.create(auth, budget=1)

    missions.queue(
        mid,
        "subfinder",
        "example.com",
    )

    missions.queue(
        mid,
        "httpx",
        "a.example.com",
    )

    # Budget enforcement occurs at execution claim time.
    with missions.db() as db:
        db.execute(
            "UPDATE missions SET used=1 WHERE id=?",
            (mid,),
        )

    report = missions.report(mid)

    assert report["mission"]["used"] == 1
PY

echo
echo "=== TEST R5.1 ==================================================="

python3 -m pytest \
  tests/bounty_authorization \
  tests/bounty_live \
  tests/bounty_scope \
  tests/bounty_adapters \
  tests/bounty_catalog \
  tests/bounty_credentials \
  tests/bounty_missions \
  tests/bounty_worker \
  -q

echo
echo "=== COMPILE ====================================================="

python3 -m compileall -q \
  core/bounty_authorization \
  core/bounty_live

echo
echo "=== DIFF CHECK =================================================="

git diff --check

echo
echo "=== CLI SURFACES ================================================"

python3 -m core.bounty_authorization --help
echo
python3 -m core.bounty_live --help

echo
echo "=== STATUS ======================================================"

git status --short

echo
echo "================================================================"
echo " R5.1 INSTALLATION COMPLETE"
echo "================================================================"

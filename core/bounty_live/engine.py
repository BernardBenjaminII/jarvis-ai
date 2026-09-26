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

import sqlite3
from types import SimpleNamespace

from core.bounty_agent.autonomy.recovery import (
    inspect_mission_integrity,
)


class Store:
    def __init__(self, path):
        self.path = path

    def db(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db


def environment(tmp_path):
    agent = Store(tmp_path / "agent.sqlite")
    live = Store(tmp_path / "live.sqlite")

    with agent.db() as db:
        db.execute("""
            CREATE TABLE sessions(
                id TEXT PRIMARY KEY,
                mission TEXT,
                authorization TEXT,
                program TEXT
            )
        """)

    with live.db() as db:
        db.execute("""
            CREATE TABLE missions(
                id TEXT PRIMARY KEY,
                authorization TEXT,
                program TEXT,
                state TEXT
            )
        """)

    return agent, live


def add_mission(live, mission="m1", auth="a1", program="p1"):
    with live.db() as db:
        db.execute(
            "INSERT INTO missions VALUES(?,?,?,'ready')",
            (mission, auth, program),
        )


def add_session(agent, session="s1", mission="m1",
                auth="a1", program="p1"):
    with agent.db() as db:
        db.execute(
            "INSERT INTO sessions VALUES(?,?,?,?)",
            (session, mission, auth, program),
        )


def test_linked_mission(tmp_path):
    agent, live = environment(tmp_path)
    add_mission(live)
    add_session(agent)

    findings = inspect_mission_integrity(agent, live)

    assert len(findings) == 1
    assert findings[0].status == "linked"


def test_orphaned_mission(tmp_path):
    agent, live = environment(tmp_path)
    add_mission(live)

    findings = inspect_mission_integrity(agent, live)

    assert findings[0].status == "orphaned"


def test_missing_mission(tmp_path):
    agent, live = environment(tmp_path)
    add_session(agent)

    findings = inspect_mission_integrity(agent, live)

    assert findings[0].status == "missing_mission"


def test_ownership_mismatch(tmp_path):
    agent, live = environment(tmp_path)
    add_mission(live, auth="a1")
    add_session(agent, auth="a2")

    findings = inspect_mission_integrity(agent, live)

    assert findings[0].status == "integrity_mismatch"


def test_multiple_sessions_ambiguous(tmp_path):
    agent, live = environment(tmp_path)
    add_mission(live)
    add_session(agent, "s1")
    add_session(agent, "s2")

    findings = inspect_mission_integrity(agent, live)

    assert findings[0].status == "ambiguous"
    assert findings[0].session_ids == ("s1", "s2")


def test_empty_databases(tmp_path):
    agent, live = environment(tmp_path)

    assert inspect_mission_integrity(agent, live) == []

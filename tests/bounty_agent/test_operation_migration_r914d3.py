import sqlite3

from core.bounty_agent.engine import BountyAgent
from core.bounty_live.engine import LiveMissionStore


def columns(path, table):
    with sqlite3.connect(path) as db:
        return {
            row[1]
            for row in db.execute(
                f"PRAGMA table_info({table})"
            )
        }


def test_fresh_live_database_has_operation_id(tmp_path):
    path = tmp_path / "live.sqlite"

    LiveMissionStore(path)

    assert "operation_id" in columns(path, "missions")


def test_fresh_agent_database_has_operation_id(tmp_path):
    path = tmp_path / "agent.sqlite"

    BountyAgent(path)

    assert "operation_id" in columns(path, "sessions")


def test_legacy_live_database_migrates(tmp_path):
    path = tmp_path / "legacy_live.sqlite"

    with sqlite3.connect(path) as db:
        db.execute("""
            CREATE TABLE missions(
                id TEXT PRIMARY KEY,
                authorization TEXT NOT NULL,
                program TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                budget INTEGER NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
            )
        """)
        db.execute("""
            INSERT INTO missions
            VALUES('legacy-m1','auth-1','training',
                   'ready',1.0,5,0)
        """)

    LiveMissionStore(path)

    with sqlite3.connect(path) as db:
        row = db.execute(
            "SELECT id,operation_id FROM missions"
        ).fetchone()

    assert row == ("legacy-m1", None)


def test_legacy_agent_database_migrates(tmp_path):
    path = tmp_path / "legacy_agent.sqlite"

    with sqlite3.connect(path) as db:
        db.execute("""
            CREATE TABLE sessions(
                id TEXT PRIMARY KEY,
                authorization TEXT NOT NULL,
                mission TEXT NOT NULL,
                program TEXT NOT NULL,
                root_target TEXT NOT NULL,
                state TEXT NOT NULL,
                created REAL NOT NULL,
                updated REAL NOT NULL,
                error TEXT
            )
        """)
        db.execute("""
            INSERT INTO sessions
            VALUES('legacy-s1','auth-1','legacy-m1',
                   'training','training.example',
                   'authorized',1.0,1.0,NULL)
        """)

    BountyAgent(path)

    with sqlite3.connect(path) as db:
        row = db.execute(
            "SELECT id,operation_id FROM sessions"
        ).fetchone()

    assert row == ("legacy-s1", None)


def test_live_operation_id_unique(tmp_path):
    path = tmp_path / "live.sqlite"
    LiveMissionStore(path)

    with sqlite3.connect(path) as db:
        for mid in ("m1", "m2"):
            db.execute("""
                INSERT INTO missions(
                    id,authorization,program,state,
                    created,budget,used
                ) VALUES(?,?,?,'ready',1.0,5,0)
            """, (mid, "auth-1", "training"))

        db.execute(
            "UPDATE missions SET operation_id='op-1' WHERE id='m1'"
        )

        try:
            db.execute(
                "UPDATE missions SET operation_id='op-1' WHERE id='m2'"
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError(
                "Duplicate operation ID was accepted"
            )


def test_agent_operation_id_unique(tmp_path):
    path = tmp_path / "agent.sqlite"
    BountyAgent(path)

    with sqlite3.connect(path) as db:
        for sid in ("s1", "s2"):
            db.execute("""
                INSERT INTO sessions(
                    id,authorization,mission,program,
                    root_target,state,created,updated,error
                ) VALUES(?,?,?,?,?,'authorized',1.0,1.0,NULL)
            """, (
                sid, "auth-1", "mission-" + sid,
                "training", "training.example",
            ))

        db.execute(
            "UPDATE sessions SET operation_id='op-1' WHERE id='s1'"
        )

        try:
            db.execute(
                "UPDATE sessions SET operation_id='op-1' WHERE id='s2'"
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError(
                "Duplicate operation ID was accepted"
            )

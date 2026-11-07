import sqlite3
import time
from types import SimpleNamespace

from core.bounty_agent.autonomy.scheduler import (
    MissionClaimStore,
)
from core.bounty_agent.autonomy.recovery import (
    inspect_pending_claims,
)


class FakeAgent:
    def __init__(self, path):
        self.path = path
        with self.db() as db:
            db.execute("""
                CREATE TABLE sessions(
                    id TEXT PRIMARY KEY,
                    authorization TEXT,
                    mission TEXT,
                    program TEXT,
                    root_target TEXT,
                    created REAL
                )
            """)

    def db(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def insert(self, session_id, mission_id, created):
        with self.db() as db:
            db.execute(
                """
                INSERT INTO sessions
                VALUES(?,?,?,?,?,?)
                """,
                (
                    session_id,
                    "auth-test",
                    mission_id,
                    "training",
                    "training.example",
                    created,
                ),
            )


def setup(tmp_path):
    claims = MissionClaimStore(
        tmp_path / "claims.sqlite"
    )
    agent = FakeAgent(tmp_path / "agent.sqlite")

    record = claims.claim(
        authorization="auth-test",
        program="training",
        target="training.example",
        policy_digest="synthetic-v1",
    )["claim"]

    return claims, agent, record


def test_unresolved_claim_remains_locked(tmp_path):
    claims, agent, record = setup(tmp_path)

    findings = inspect_pending_claims(claims, agent)

    assert len(findings) == 1
    assert findings[0].status == "unresolved"
    assert claims.get(record["claim_key"])["state"] == "claimed"


def test_single_session_is_candidate_only(tmp_path):
    claims, agent, record = setup(tmp_path)

    agent.insert(
        "session-1",
        "mission-1",
        record["created"] + 1,
    )

    findings = inspect_pending_claims(claims, agent)

    assert findings[0].status == "candidate_match"
    assert findings[0].session_ids == ("session-1",)
    assert findings[0].mission_ids == ("mission-1",)
    assert claims.get(record["claim_key"])["state"] == "claimed"


def test_multiple_sessions_are_ambiguous(tmp_path):
    claims, agent, record = setup(tmp_path)

    for index in (1, 2):
        agent.insert(
            f"session-{index}",
            f"mission-{index}",
            record["created"] + index,
        )

    findings = inspect_pending_claims(claims, agent)

    assert findings[0].status == "ambiguous"
    assert len(findings[0].session_ids) == 2


def test_preexisting_session_not_adopted(tmp_path):
    claims, agent, record = setup(tmp_path)

    agent.insert(
        "old-session",
        "old-mission",
        record["created"] - 100,
    )

    findings = inspect_pending_claims(claims, agent)

    assert findings[0].status == "unresolved"

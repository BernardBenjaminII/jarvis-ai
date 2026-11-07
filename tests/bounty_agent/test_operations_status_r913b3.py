import time
from types import SimpleNamespace

from core.bounty_authorization import AuthorizationDenied
from core.bounty_agent.operations_status import (
    build_operations_status,
)


class FakeAuthorizationStore:
    def __init__(self, revoked=False, expired=False):
        self.revoked = revoked
        self.expires = time.time() + (
            -3600 if expired else 3600
        )

    def get(self, authorization_id):
        assert authorization_id == "auth-1"
        return {
            "revoked": int(self.revoked),
            "expires": self.expires,
        }

    def live_scope(self, authorization_id):
        if self.revoked or self.expires <= time.time():
            raise AuthorizationDenied("Not authorized")
        return object()


class FakeLiveStore:
    def interrupted_candidates(self, *, older_than):
        assert older_than == 300
        return [
            {"id": "task-3", "mission": "mission-1"},
            {"id": "other", "mission": "mission-2"},
        ]


class FakeAgent:
    def __init__(self, **kwargs):
        self.authorization_store = (
            FakeAuthorizationStore(**kwargs)
        )
        self.live_store = FakeLiveStore()

    def report(self, session_id):
        assert session_id == "session-1"
        return {
            "session": {
                "id": "session-1",
                "authorization": "auth-1",
                "mission": "mission-1",
                "state": "options_ready",
            },
            "mission": {
                "mission": {
                    "budget": 5,
                    "used": 2,
                },
                "tasks": [
                    {"state": "completed"},
                    {"state": "completed"},
                    {"state": "running"},
                ],
            },
            "options": [
                {"state": "awaiting_human"},
                {"state": "hold"},
            ],
        }


def test_operations_status_valid():
    result = build_operations_status(
        FakeAgent(),
        "session-1",
    )

    assert result["authorization"]["status"] == "valid"
    assert result["tasks"]["completed"] == 2
    assert result["tasks"]["running"] == 1
    assert result["awaiting_human"] == 1
    assert result["target_budget"] == 5
    assert result["execution_units_used"] == 2

    recovery = result["recovery"]
    assert len(recovery["potentially_abandoned"]) == 1
    assert recovery["automatic_retry_allowed"] is False


def test_operations_status_revoked():
    result = build_operations_status(
        FakeAgent(revoked=True),
        "session-1",
    )

    assert result["authorization"]["status"] == "revoked"


def test_operations_status_expired():
    result = build_operations_status(
        FakeAgent(expired=True),
        "session-1",
    )

    assert result["authorization"]["status"] == "expired"


def test_operations_status_contains_no_scope_document():
    result = build_operations_status(
        FakeAgent(),
        "session-1",
    )

    assert "scope_json" not in result["authorization"]
    assert "password" not in result
    assert "token" not in result

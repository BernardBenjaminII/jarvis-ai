from types import SimpleNamespace

from core.bounty_agent.autonomy.authorization_bridge import (
    Candidate,
    AuthorizationBinding,
    select_authorized_candidate,
)


class FakeStore:
    def __init__(self, scopes):
        self.scopes = scopes

    def live_scope(self, authorization_id):
        return self.scopes[authorization_id]


def scope(program, permitted=True):
    return SimpleNamespace(
        program=program,
        logical_capabilities=("subdomain_discovery",),
        permits_host=lambda host: permitted,
        require=lambda host, capability: host,
    )


def binding(program, target, auth="auth-1", **kwargs):
    return AuthorizationBinding(
        authorization_id=auth,
        program=program,
        target=target,
        reviewed=kwargs.get("reviewed", True),
        active=kwargs.get("active", True),
    )


def test_selects_authorized_candidate():
    result = select_authorized_candidate(
        [Candidate("demo", "demo.example", 90)],
        [binding("demo", "demo.example")],
        scope_store=FakeStore({"auth-1": scope("demo")}),
    )
    assert result["status"] == "authorized_candidate_selected"
    assert result["execution_started"] is False


def test_rejects_unreviewed():
    result = select_authorized_candidate(
        [Candidate("demo", "demo.example", 90)],
        [binding("demo", "demo.example", reviewed=False)],
        scope_store=FakeStore({"auth-1": scope("demo")}),
    )
    assert result["status"] == "no_authorized_candidate"


def test_rejects_scope_mismatch():
    result = select_authorized_candidate(
        [Candidate("demo", "demo.example", 90)],
        [binding("demo", "demo.example")],
        scope_store=FakeStore({
            "auth-1": scope("demo", permitted=False)
        }),
    )
    assert result["status"] == "no_authorized_candidate"


def test_rejects_wrong_program():
    result = select_authorized_candidate(
        [Candidate("demo", "demo.example", 90)],
        [binding("other", "demo.example")],
        scope_store=FakeStore({"auth-1": scope("other")}),
    )
    assert result["status"] == "no_authorized_candidate"


def test_prefers_highest_ranked_authorized():
    result = select_authorized_candidate(
        [
            Candidate("blocked", "blocked.example", 100),
            Candidate("eligible", "eligible.example", 80),
        ],
        [binding("eligible", "eligible.example")],
        scope_store=FakeStore({
            "auth-1": scope("eligible")
        }),
    )
    assert result["program"] == "eligible"

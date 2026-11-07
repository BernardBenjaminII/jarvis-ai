import pytest

from core.bounty_agent.autonomy.lab_authorization_r917 import (
    LocalLabAuthorization,
    LabAuthorizationError,
)


def test_approved_local_lab():
    authorization = LocalLabAuthorization(
        target="http://127.0.0.1:3000/",
        method="GET",
        path="/",
        approved=True,
    )
    assert authorization.require() is True


@pytest.mark.parametrize("target", [
    "http://localhost:3000/",
    "http://127.0.0.2:3000/",
    "http://127.0.0.1:8000/",
    "https://127.0.0.1:3000/",
    "http://example.com/",
    "http://127.0.0.1:3000@evil.example/",
    "http://127.0.0.1:3000/other",
])
def test_rejects_other_targets(target):
    with pytest.raises(LabAuthorizationError):
        LocalLabAuthorization(
            target=target,
            method="GET",
            path="/",
            approved=True,
        ).require()


def test_rejects_unapproved_lab():
    with pytest.raises(LabAuthorizationError):
        LocalLabAuthorization(
            target="http://127.0.0.1:3000/",
            method="GET",
            path="/",
            approved=False,
        ).require()


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_rejects_other_methods(method):
    with pytest.raises(LabAuthorizationError):
        LocalLabAuthorization(
            target="http://127.0.0.1:3000/",
            method=method,
            path="/",
            approved=True,
        ).require()

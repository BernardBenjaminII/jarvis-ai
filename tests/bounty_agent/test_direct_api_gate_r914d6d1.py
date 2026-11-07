"""R9.14D.6D.1: direct API execution paths fail closed."""

import pytest
from fastapi import HTTPException

from core.src.routes.bounty_agent import (
    CreateRequest,
    create_session,
    run_session,
)


def test_direct_creation_disabled(monkeypatch):
    def forbidden_agent():
        raise AssertionError("Agent must not be instantiated")

    monkeypatch.setattr(
        "core.src.routes.bounty_agent._agent",
        forbidden_agent,
    )

    request = CreateRequest(
        authorization_id="synthetic-auth",
        root_target="training.example",
        budget=2,
    )

    with pytest.raises(HTTPException) as error:
        create_session(request)

    assert error.value.status_code == 403


def test_direct_recon_disabled(monkeypatch):
    def forbidden_agent():
        raise AssertionError("Agent must not be instantiated")

    monkeypatch.setattr(
        "core.src.routes.bounty_agent._agent",
        forbidden_agent,
    )

    with pytest.raises(HTTPException) as error:
        run_session("synthetic-session")

    assert error.value.status_code == 403

import base64

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.bounty_agent.autonomy.program_scope_r921a import (
    ScopeIntakeError,
    assess_scope_target,
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_review_r921b import (
    review_scope_draft,
    assess_reviewed_target,
)
from core.bounty_agent.http_access import require_bounty_access
from core.src.routes.program_scopes_r921d import router


def payload():
    return {
        "platform": "intigriti",
        "program": "Synthetic Intigriti Test",
        "policy_url": (
            "https://app.intigriti.com/programs/"
            "training/synthetic/detail"
        ),
        "in_scope": ["api.training.example"],
        "out_of_scope": ["admin.training.example"],
        "restrictions": [
            "No automated scanning without approval"
        ],
    }


def test_intigriti_draft():
    draft = create_scope_draft(**payload())
    assert draft["platform"] == "intigriti"
    assert draft["scope_verified"] is False
    assert draft["execution_authorized"] is False


def test_exclusion():
    draft = create_scope_draft(**payload())
    result = assess_scope_target(
        draft, "admin.training.example"
    )
    assert result["classification"] == "explicitly_excluded"


@pytest.mark.parametrize("url", [
    "http://app.intigriti.com/programs/test",
    "https://app.intigriti.com.evil.example/programs/test",
    "https://intigriti.com.evil.example/programs/test",
    "https://evil.example/programs/test",
    "https://user:pass@app.intigriti.com/programs/test",
])
def test_invalid_policy_urls(url):
    data = payload()
    data["policy_url"] = url
    with pytest.raises(ScopeIntakeError):
        create_scope_draft(**data)


def test_review_still_cannot_authorize_execution():
    from datetime import datetime, timezone

    draft = create_scope_draft(**payload())
    review = review_scope_draft(
        draft,
        reviewer="synthetic-operator",
        source_checked_at=datetime.now(
            timezone.utc
        ).isoformat(),
        source_matches=True,
    )
    result = assess_reviewed_target(
        draft, review, "api.training.example"
    )
    assert result["advisory_eligible"] is True
    assert result["testing_authorized"] is False
    assert result["execution_authorized"] is False


def test_authenticated_api_import(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("JARVIS_BOUNTY_USER", "test-user")
    monkeypatch.setenv(
        "JARVIS_BOUNTY_PASSWORD",
        "synthetic-password-" + "x" * 40,
    )

    app = FastAPI()
    app.include_router(
        router,
        prefix="/api/bounty-agent",
        dependencies=[Depends(require_bounty_access)],
    )
    client = TestClient(app)

    path = "/api/bounty-agent/program-scopes"

    assert client.post(
        path, json=payload()
    ).status_code == 401

    token = base64.b64encode(
        ("test-user:synthetic-password-" + "x" * 40)
        .encode()
    ).decode()

    response = client.post(
        path,
        json=payload(),
        headers={"Authorization": "Basic " + token},
    )

    assert response.status_code == 201
    assert response.json()["scope_verified"] is False
    assert response.json()["execution_authorized"] is False
    assert response.json()["submission_authorized"] is False

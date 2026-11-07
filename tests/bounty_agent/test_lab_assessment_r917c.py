import pytest

from core.bounty_agent.autonomy.lab_assessment_r917 import (
    assess_local_headers,
)
from core.bounty_agent.autonomy.lab_authorization_r917 import (
    LocalLabAuthorization,
)


def test_local_header_assessment(tmp_path, monkeypatch):
    import http.client

    class FakeSocket:
        def getpeername(self):
            return ("127.0.0.1", 3000)

    class FakeResponse:
        status = 200

        def getheaders(self):
            return [
                ("Content-Type", "text/html"),
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "SAMEORIGIN"),
            ]

    class FakeConnection:
        sock = FakeSocket()

        def __init__(self, *args, **kwargs):
            pass

        def connect(self):
            pass

        def request(self, *args, **kwargs):
            pass

        def getresponse(self):
            return FakeResponse()

        def close(self):
            pass

    monkeypatch.setattr(
        http.client, "HTTPConnection", FakeConnection
    )

    authorization = LocalLabAuthorization(
        target="http://127.0.0.1:3000/",
        method="GET",
        path="/",
        approved=True,
    )

    result = assess_local_headers(
        authorization=authorization,
        evidence_dir=tmp_path,
    )

    assert len(result["findings"]) == 1
    assert result["findings"][0]["header"] == "content-security-policy"
    assert (
        result["findings"][0]["classification"]
        == "security_hardening_observation"
    )
    assert result["findings"][0]["validated_vulnerability"] is False

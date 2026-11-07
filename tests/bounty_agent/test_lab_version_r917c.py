import hashlib
import http.client
import json

import pytest

from core.bounty_agent.autonomy.lab_version_r917 import (
    VersionLabAuthorization,
    verify_local_version,
)
from core.bounty_agent.autonomy.local_lab_r917 import LabBoundaryError


def authorization(approved=True):
    return VersionLabAuthorization(
        target="http://127.0.0.1:3000/rest/admin/application-version",
        method="GET",
        path="/rest/admin/application-version",
        approved=approved,
    )


def test_rejects_unapproved_request(tmp_path, monkeypatch):
    def forbidden_connect(self):
        raise AssertionError("Network must not be accessed")

    monkeypatch.setattr(
        http.client.HTTPConnection, "connect", forbidden_connect
    )

    with pytest.raises(LabBoundaryError, match="not authorized"):
        verify_local_version(
            authorization=authorization(False),
            evidence_dir=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_version_evidence_integrity(tmp_path, monkeypatch):
    class FakeSocket:
        def getpeername(self):
            return ("127.0.0.1", 3000)

    class FakeResponse:
        status = 200

        def read(self, size):
            return b'{"version":"20.3.0"}'

        def getheaders(self):
            return [("Content-Type", "application/json")]

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

    result = verify_local_version(
        authorization=authorization(),
        evidence_dir=tmp_path,
    )

    evidence = tmp_path / result["evidence_path"].split("/")[-1]
    content = evidence.read_bytes()
    payload = json.loads(content)

    assert hashlib.sha256(content).hexdigest() == result["sha256"]
    assert payload["version"] == "20.3.0"
    assert payload["validated_vulnerability"] is False
    assert payload["submission_authorized"] is False


def test_network_failure_creates_no_evidence(tmp_path, monkeypatch):
    def fail_connect(self):
        raise ConnectionRefusedError("Lab unavailable")

    monkeypatch.setattr(
        http.client.HTTPConnection, "connect", fail_connect
    )

    with pytest.raises(LabBoundaryError, match="request failed"):
        verify_local_version(
            authorization=authorization(),
            evidence_dir=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []

import pytest

from core.bounty_agent.autonomy.local_lab_r917 import (
    LabBoundaryError,
    observe_local_juice_shop,
)


@pytest.mark.parametrize("timeout", [
    0, -1, 11, True, "5", None,
])
def test_rejects_invalid_timeout(tmp_path, timeout):
    with pytest.raises(LabBoundaryError):
        observe_local_juice_shop(
            evidence_dir=tmp_path,
            timeout=timeout,
        )


def test_rejects_missing_evidence_directory(tmp_path):
    with pytest.raises(LabBoundaryError):
        observe_local_juice_shop(
            evidence_dir=tmp_path / "missing",
        )

from core.bounty_agent.autonomy.lab_authorization_r917 import (
    LocalLabAuthorization,
    LabAuthorizationError,
)


def test_missing_authorization_blocks_execution(tmp_path, monkeypatch):
    def forbidden_connect(*args, **kwargs):
        raise AssertionError("Network must not be accessed")

    monkeypatch.setattr(
        "http.client.HTTPConnection.connect",
        forbidden_connect,
    )

    with pytest.raises(LabBoundaryError, match="authorization"):
        observe_local_juice_shop(evidence_dir=tmp_path)


def test_unapproved_authorization_blocks_execution(tmp_path, monkeypatch):
    def forbidden_connect(*args, **kwargs):
        raise AssertionError("Network must not be accessed")

    monkeypatch.setattr(
        "http.client.HTTPConnection.connect",
        forbidden_connect,
    )

    authorization = LocalLabAuthorization(
        target="http://127.0.0.1:3000/",
        method="GET",
        path="/",
        approved=False,
    )

    with pytest.raises(LabAuthorizationError):
        observe_local_juice_shop(
            evidence_dir=tmp_path,
            authorization=authorization,
        )


def test_external_target_blocks_execution(tmp_path, monkeypatch):
    def forbidden_connect(*args, **kwargs):
        raise AssertionError("Network must not be accessed")

    monkeypatch.setattr(
        "http.client.HTTPConnection.connect",
        forbidden_connect,
    )

    authorization = LocalLabAuthorization(
        target="http://example.com/",
        method="GET",
        path="/",
        approved=True,
    )

    with pytest.raises(LabAuthorizationError):
        observe_local_juice_shop(
            evidence_dir=tmp_path,
            authorization=authorization,
        )


def test_redirect_is_rejected(tmp_path, monkeypatch):
    import http.client

    class FakeResponse:
        status = 302

        def getheader(self, name):
            return "text/html"

        def read(self, size):
            return b""

    class FakeSocket:
        def getpeername(self):
            return ("127.0.0.1", 3000)

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
        http.client,
        "HTTPConnection",
        FakeConnection,
    )

    authorization = LocalLabAuthorization(
        target="http://127.0.0.1:3000/",
        method="GET",
        path="/",
        approved=True,
    )

    with pytest.raises(LabBoundaryError, match="redirect"):
        observe_local_juice_shop(
            evidence_dir=tmp_path,
            authorization=authorization,
        )

    assert list(tmp_path.iterdir()) == []


def test_connection_failure_creates_no_evidence(tmp_path, monkeypatch):
    import http.client

    def fail_connect(self):
        raise ConnectionRefusedError("Simulated unavailable lab")

    monkeypatch.setattr(
        http.client.HTTPConnection,
        "connect",
        fail_connect,
    )

    authorization = LocalLabAuthorization(
        target="http://127.0.0.1:3000/",
        method="GET",
        path="/",
        approved=True,
    )

    with pytest.raises(LabBoundaryError, match="request failed"):
        observe_local_juice_shop(
            evidence_dir=tmp_path,
            authorization=authorization,
        )

    assert list(tmp_path.iterdir()) == []


def test_invalid_evidence_path_blocks_network(tmp_path, monkeypatch):
    import http.client

    def forbidden_connect(self):
        raise AssertionError("Network must not be accessed")

    monkeypatch.setattr(
        http.client.HTTPConnection,
        "connect",
        forbidden_connect,
    )

    authorization = LocalLabAuthorization(
        target="http://127.0.0.1:3000/",
        method="GET",
        path="/",
        approved=True,
    )

    with pytest.raises(LabBoundaryError, match="Evidence directory"):
        observe_local_juice_shop(
            evidence_dir=tmp_path / "nonexistent",
            authorization=authorization,
        )

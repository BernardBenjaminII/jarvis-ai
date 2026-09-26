from core.bounty_scope import LiveScope
from core.bounty_adapters import subfinder, httpx


def scope():
    return LiveScope.reviewed(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        allowed_capabilities=["subfinder", "httpx"],
        reviewed_by="tester",
        source_material="synthetic reviewed fixture",
    )


def test_subfinder_filters_output(monkeypatch):
    monkeypatch.setattr(
        subfinder,
        "binary",
        lambda name: "/test/subfinder",
    )

    monkeypatch.setattr(
        subfinder,
        "execute",
        lambda argv, **kw: {
            "state": "completed",
            "returncode": 0,
            "bytes": 64,
            "output": (
                "a.example.com\n"
                "private.example.com\n"
                "outside.example.org\n"
            ),
        },
    )

    result = subfinder.enumerate_subdomains(
        scope(),
        "example.com",
    )

    assert result["accepted"] == ["a.example.com"]

    assert set(result["rejected"]) == {
        "private.example.com",
        "outside.example.org",
    }

    assert result["state"] == "completed"


def test_httpx_fixed_target(monkeypatch):
    seen = {}

    monkeypatch.setattr(
        httpx,
        "binary",
        lambda name: "/test/httpx",
    )

    def fake(argv, **kw):
        seen["argv"] = argv

        return {
            "state": "completed",
            "returncode": 0,
            "bytes": 40,
            "output": '{"url":"https://a.example.com","status_code":200}\n',
        }

    monkeypatch.setattr(httpx, "execute", fake)

    result = httpx.probe_http(
        scope(),
        "a.example.com",
    )

    assert seen["argv"] == [
        "/test/httpx",
        "-silent",
        "-u",
        "https://a.example.com",
        "-json",
        "-no-color",
    ]

    assert result["records"][0]["status_code"] == 200


def test_httpx_does_not_enable_redirects(monkeypatch):
    seen = {}

    monkeypatch.setattr(
        httpx,
        "binary",
        lambda name: "/test/httpx",
    )

    def fake(argv, **kw):
        seen["argv"] = argv

        return {
            "state": "completed",
            "returncode": 0,
            "bytes": 0,
            "output": "",
        }

    monkeypatch.setattr(httpx, "execute", fake)

    httpx.probe_http(
        scope(),
        "a.example.com",
    )

    assert "-follow-redirects" not in seen["argv"]
    assert "-fr" not in seen["argv"]

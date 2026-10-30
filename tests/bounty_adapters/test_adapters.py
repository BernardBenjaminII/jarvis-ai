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


def test_dnsx_fixed_target_and_scope_filter(monkeypatch):
    from core.bounty_adapters import dnsx

    seen = {}

    s = LiveScope.reviewed(
        program="dns-demo",
        include=[
            "example.com",
            "*.example.com",
        ],
        logical_capabilities=[
            "dns_resolution",
        ],
        approved_providers=[
            "dnsx",
        ],
        reviewed_by="tester",
        source_material="dns synthetic fixture",
    )

    monkeypatch.setattr(
        dnsx,
        "binary",
        lambda name: "/test/dnsx",
    )

    def fake(argv, **kw):
        seen["argv"] = argv
        seen["stdin_text"] = kw.get(
            "stdin_text"
        )

        return {
            "state": "completed",
            "returncode": 0,
            "bytes": 128,
            "output": (
                '{"host":"a.example.com",'
                '"a":["192.0.2.10"]}\n'
                '{"host":"outside.example.org",'
                '"a":["192.0.2.20"]}\n'
            ),
        }

    monkeypatch.setattr(
        dnsx,
        "execute",
        fake,
    )

    result = dnsx.resolve_dns(
        s,
        "a.example.com",
    )

    assert seen["argv"] == [
        "/test/dnsx",
        "-silent",
        "-a",
        "-json",
    ]

    assert "-d" not in seen["argv"]

    assert (
        seen["stdin_text"]
        == "a.example.com\n"
    )

    assert result["accepted"] == [
        "a.example.com"
    ]

    assert result["rejected"] == [
        "outside.example.org"
    ]

    assert len(result["records"]) == 2


def test_dnsx_requires_provider_authorization(
    monkeypatch,
):
    from core.bounty_adapters import dnsx
    import pytest
    from core.bounty_scope import ScopeDenied

    s = LiveScope.reviewed(
        program="dns-denied",
        include=["example.com"],
        logical_capabilities=[
            "http_probe",
        ],
        approved_providers=[
            "httpx",
        ],
        reviewed_by="tester",
        source_material="dns denied fixture",
    )

    with pytest.raises(ScopeDenied):
        dnsx.resolve_dns(
            s,
            "example.com",
        )

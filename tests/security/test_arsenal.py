from core.security import arsenal


def test_snapshot_derives_capabilities(monkeypatch):
    paths = {
        "subfinder": "/usr/bin/subfinder",
        "nmap": "/usr/bin/nmap",
        "dig": "/usr/bin/dig",
    }

    monkeypatch.setattr(
        arsenal.shutil,
        "which",
        lambda command: paths.get(command),
    )

    monkeypatch.setattr(
        arsenal,
        "_httpx_recon_available",
        lambda: False,
    )

    snapshot = arsenal.build_arsenal_snapshot()

    capabilities = {
        item["id"]: item
        for item in snapshot["capabilities"]
    }

    assert capabilities["subdomain_discovery"]["available"] is True
    assert capabilities["port_discovery"]["available"] is True
    assert capabilities["service_enumeration"]["available"] is True
    assert capabilities["domain_intelligence"]["available"] is True
    assert capabilities["template_scanning"]["available"] is False


def test_httpx_requires_verified_identity(monkeypatch):
    monkeypatch.setattr(
        arsenal.shutil,
        "which",
        lambda command: (
            "/usr/bin/httpx"
            if command == "httpx"
            else None
        ),
    )

    monkeypatch.setattr(
        arsenal,
        "_httpx_recon_available",
        lambda: False,
    )

    snapshot = arsenal.build_arsenal_snapshot()

    httpx = next(
        tool
        for tool in snapshot["tools"]
        if tool["id"] == "httpx"
    )

    assert httpx["present"] is True
    assert httpx["available"] is False


def test_httpx_verified_recon_identity(monkeypatch):
    monkeypatch.setattr(
        arsenal.shutil,
        "which",
        lambda command: (
            "/usr/local/bin/httpx"
            if command == "httpx"
            else None
        ),
    )

    monkeypatch.setattr(
        arsenal,
        "_httpx_recon_available",
        lambda: True,
    )

    snapshot = arsenal.build_arsenal_snapshot()

    httpx = next(
        tool
        for tool in snapshot["tools"]
        if tool["id"] == "httpx"
    )

    assert httpx["present"] is True
    assert httpx["available"] is True


def test_arsenal_inventory_does_not_execute_tools(monkeypatch):
    called = []

    def fake_which(command):
        called.append(command)
        return None

    monkeypatch.setattr(
        arsenal.shutil,
        "which",
        fake_which,
    )

    monkeypatch.setattr(
        arsenal,
        "_httpx_recon_available",
        lambda: False,
    )

    snapshot = arsenal.build_arsenal_snapshot()

    assert snapshot["summary"]["defined_tools"] == len(
        arsenal.TOOLS
    )
    assert set(called) == {
        tool.command for tool in arsenal.TOOLS
    }

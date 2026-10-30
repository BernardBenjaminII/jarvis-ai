from core.src.routes import platform_workspace as route_module


def test_api_payload_kali(monkeypatch):
    monkeypatch.setattr(
        route_module,
        "detect_platform",
        lambda: {
            "environment": "kali",
            "distribution": "kali",
            "pretty_name": "Kali GNU/Linux",
        },
    )

    monkeypatch.setattr(
        route_module,
        "get_current_workspace",
        lambda: route_module.get_platform_workspace("kali"),
    )

    payload = route_module.build_workspace_payload()

    assert payload["platform"]["environment"] == "kali"

    workspace = payload["workspace"]

    assert workspace["workspace_id"] == "kali-security"
    assert workspace["stance"] == "security"
    assert workspace["execution_enabled"] is True

    assert "bounties" in workspace["navigation"]
    assert "recon" in workspace["navigation"]
    assert "arsenal" in workspace["navigation"]


def test_api_payload_unknown_platform_fails_closed(monkeypatch):
    monkeypatch.setattr(
        route_module,
        "detect_platform",
        lambda: {
            "environment": "plan9",
        },
    )

    monkeypatch.setattr(
        route_module,
        "get_current_workspace",
        lambda: route_module.get_platform_workspace("plan9"),
    )

    payload = route_module.build_workspace_payload()

    workspace = payload["workspace"]

    assert workspace["execution_enabled"] is False
    assert "recon" not in workspace["navigation"]
    assert "bounties" not in workspace["navigation"]


def test_platform_lookup_does_not_enable_kali_on_ubuntu():
    payload = route_module.platform_workspace_for("ubuntu")

    workspace = payload["workspace"]

    assert workspace["platform"] == "ubuntu"
    assert workspace["workspace_id"] == "ubuntu-engineering"
    assert "bounties" not in workspace["navigation"]
    assert "recon" not in workspace["navigation"]


def test_kali_navigation_order_is_stable():
    payload = route_module.platform_workspace_for("kali")

    assert payload["workspace"]["navigation"] == [
        "missions",
        "bounties",
        "targets",
        "recon",
        "findings",
        "agents",
        "intelligence",
        "arsenal",
        "terminal",
        "knowledge",
        "system",
    ]

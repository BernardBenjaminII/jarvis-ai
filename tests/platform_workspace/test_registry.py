from core.platform_workspace.registry import get_platform_workspace


def test_kali_workspace_identity():
    workspace = get_platform_workspace("kali")

    assert workspace.platform == "kali"
    assert workspace.workspace_id == "kali-security"
    assert workspace.stance == "security"
    assert workspace.execution_enabled is True


def test_kali_workspace_contains_security_navigation():
    workspace = get_platform_workspace("kali")

    expected = {
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
    }

    assert expected.issubset(set(workspace.navigation))


def test_kali_recon_is_executable():
    workspace = get_platform_workspace("kali")

    assert workspace.capabilities["recon"].enabled is True
    assert workspace.capabilities["recon"].execution is True


def test_ubuntu_does_not_inherit_kali_security_workspace():
    workspace = get_platform_workspace("ubuntu")

    assert workspace.workspace_id != "kali-security"
    assert "recon" not in workspace.navigation
    assert "bounties" not in workspace.navigation


def test_unknown_platform_fails_closed():
    workspace = get_platform_workspace("plan9")

    assert workspace.execution_enabled is False
    assert "recon" not in workspace.navigation
    assert "bounties" not in workspace.navigation

from core.bootstrap.discovery.platform import detect_platform_details
from core.src.routes import bounty_agent as route_module

def test_r7_platform_contract():
    payload = route_module.bounty_agent_platform()
    assert "environment" in payload
    assert "live_bounty_enabled" in payload
    assert payload["live_bounty_enabled"] == (payload["environment"] == "kali")

def test_platform_detector_contract():
    details = detect_platform_details()
    assert "environment" in details

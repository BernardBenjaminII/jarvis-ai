from __future__ import annotations

from core.src.cognition.capability_registry import detect_capabilities


def verify_capabilities():



    print("Checking capabilities...")



    capabilities = detect_capabilities()



    for capability, available in capabilities.items():



        status = "✓" if available else "✗"



        print(f"{status} {capability}")



    return capabilities

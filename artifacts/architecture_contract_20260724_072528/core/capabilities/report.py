from __future__ import annotations

from core.capabilities.models import CapabilityResult


def print_capability_report(results: list[CapabilityResult]) -> None:
    print()
    print("=" * 70)
    print("JARVIS CAPABILITY REPORT")
    print("=" * 70)

    for result in results:
        print()
        print(result.name)
        print("-" * len(result.name))
        print(f"Success : {result.success}")
        print(f"Elapsed : {result.elapsed:.2f}s")

        for key, value in result.metrics.items():
            print(f"{key}: {value}")

        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")

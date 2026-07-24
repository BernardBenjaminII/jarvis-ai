from __future__ import annotations

from pathlib import Path
import yaml


OWNERSHIP_FILE = Path("knowledge/architecture/canonical_owners.yaml")


def main() -> None:
    data = yaml.safe_load(OWNERSHIP_FILE.read_text(encoding="utf-8"))
    capabilities = data.get("capabilities", {})

    print("=" * 70)
    print("JARVIS KNOWLEDGE CAPABILITY OWNERSHIP")
    print("=" * 70)
    print()

    for name, body in sorted(capabilities.items()):
        print(f"{name:<18} {body['owner']:<25} {body['role']}")

    print()
    print(f"[OK] Capabilities defined: {len(capabilities)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse

from dev.librarian.discovery.engine import discover, write_discovery_plan


def main() -> None:
    ap = argparse.ArgumentParser(description="JARVIS Knowledge Discovery Engine")
    ap.add_argument("topic", help="Topic to research, e.g. linear algebra, field medicine, cybersecurity")
    ap.add_argument("--max", type=int, default=50)
    args = ap.parse_args()

    candidates = discover(args.topic, max_candidates=args.max)
    plan_path = write_discovery_plan(args.topic, candidates)

    print(f"\nJARVIS Discovery Plan: {args.topic}")
    print("=" * 60)

    if not candidates:
        print("No trusted source candidates found.")
        return

    for i, c in enumerate(candidates, 1):
        print(f"\n{i}. {c.source_name}  priority={c.priority}")
        print(f"   method: {c.method}")
        print(f"   query : {c.query}")
        print(f"   reason: {c.reason}")

    print(f"\n[OK] Plan written: {plan_path}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from core.bootstrap.main import main

"""
Runtime launcher.

This module intentionally forwards execution to the canonical bootstrap:

    core.bootstrap.main

It exists for backward compatibility with older launch scripts.
"""

if __name__ == "__main__":
    main()

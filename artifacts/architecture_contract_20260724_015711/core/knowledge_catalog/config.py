"""
Knowledge Catalog configuration
"""

from pathlib import Path

# Main metadata catalog
DEFAULT_CATALOG_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

# Knowledge repository
DEFAULT_KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

# Download staging area
DEFAULT_DOWNLOAD_ROOT = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge"
)

# Reports
DEFAULT_REPORT_DIR = DEFAULT_KNOWLEDGE_ROOT / "manifests"

# SQLite timeout
SQLITE_TIMEOUT = 30

# Trust tiers
TRUST_TIER_GOLD = 0
TRUST_TIER_SILVER = 1
TRUST_TIER_BRONZE = 2

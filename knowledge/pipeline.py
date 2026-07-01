from pathlib import Path

from knowledge.processing import ProcessingEngine


def run_inventory(knowledge_root: Path, catalog_path: Path) -> dict:
    """
    Compatibility wrapper for the CLI.

    The old name 'run_inventory' is preserved for now, but internally this
    now runs the ProcessingEngine foundation stages:
    catalog -> inspect -> structure.
    """

    engine = ProcessingEngine(catalog_path)
    return engine.run_foundation(knowledge_root)

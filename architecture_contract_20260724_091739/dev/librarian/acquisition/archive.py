import shutil
from pathlib import Path


def archive(original: Path, archive_root: Path):

    archive_root.mkdir(parents=True, exist_ok=True)

    shutil.move(str(original), archive_root / original.name)

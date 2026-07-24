from pathlib import Path
from collections import defaultdict

from core.knowledge_mapper.mapper import map_path

SUPPORTED = {
    ".pdf",
    ".txt",
    ".md",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".epub",
    ".zim",
}


def build_subject_index(root: Path):

    subject_index = defaultdict(list)

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED:
            continue

        mapping = map_path(str(path))

        subject = mapping["subject"]

        subject_index[subject].append(path)

    return subject_index

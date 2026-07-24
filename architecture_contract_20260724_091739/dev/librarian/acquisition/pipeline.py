from pathlib import Path

from normalize import normalize
from filter import should_keep
from metadata import extract_json_metadata


def process(download):

    extracted = normalize(
        download,
        Path("/tmp/jarvis")
    )

    metadata = extract_json_metadata(extracted)

    keep = []

    for f in extracted.rglob("*"):

        if f.is_file() and should_keep(f):

            keep.append(f)

    return metadata, keep

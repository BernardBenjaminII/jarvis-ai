from pathlib import Path
import csv
from collections import Counter

ROOT = Path("/media/abdullah/JARVISDATA/Knowledge")
OUT = Path("knowledge/reports/library_inventory.csv")

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".jarvis",
    "AUXFILES",
    "INFO",
    "PREVIEW",
}

DOC_EXT = {
    ".pdf",
    ".epub",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".xml",
}

DATA_EXT = {
    ".tif",
    ".tiff",
    ".img",
    ".dem",
    ".hgt",
    ".csv",
    ".geojson",
    ".json",
    ".zip",
    ".7z",
    ".tar",
    ".gz",
}

SPECIAL_EXT = {
    ".zim",
}


rows = []

for directory in sorted(ROOT.rglob("*")):

    if not directory.is_dir():
        continue

    if any(part in IGNORE_DIRS for part in directory.parts):
        continue

    counts = Counter()

    for f in directory.rglob("*"):

        if not f.is_file():
            continue

        ext = f.suffix.lower()

        if ext in DOC_EXT:
            counts["documents"] += 1

        elif ext in DATA_EXT:
            counts["datasets"] += 1

        elif ext in SPECIAL_EXT:
            counts["zim"] += 1

        else:
            counts["other"] += 1

    total = sum(counts.values())

    if total == 0:
        continue

    rows.append({
        "folder": str(directory.relative_to(ROOT)),
        "documents": counts["documents"],
        "datasets": counts["datasets"],
        "zim": counts["zim"],
        "other": counts["other"],
        "total": total,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "folder",
            "documents",
            "datasets",
            "zim",
            "other",
            "total",
        ],
    )

    writer.writeheader()
    writer.writerows(rows)

print(f"[OK] wrote {OUT}")
print(f"[OK] folders: {len(rows)}")

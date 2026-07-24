from pathlib import Path

KEEP_SUFFIXES = {
    ".pdf",
    ".epub",
    ".txt",
    ".md",
    ".json",
    ".csv",
    ".xml",
}

KEEP_HTML_NAMES = {
    "syllabus",
    "assignments",
    "exams",
    "readings",
    "calendar",
    "study-materials",
    "lecture-notes",
    "lecture-notes.html",
    "index.html",
}

DROP_SUFFIXES = {
    ".css",
    ".js",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".mp4",
    ".mov",
    ".webm",
    ".vtt",
    ".srt",
}

DROP_PARTS = {
    "static_shared",
    "static_resources",
    "favicon.ico",
    "video_galleries",
    "videos",
    "lecture-videos",
    "video_placeholder",
    "mathjax",
    "fonts",
    "css",
    "js",
}

KEEP_PARTS = {
    "assignments",
    "exams",
    "readings",
    "study-materials",
    "problem-set-solutions",
    "exam-solutions",
    "lecture-notes",
    "resources",
    "pages",
}


def should_keep(path: Path) -> bool:
    suffix = path.suffix.lower()
    parts = {p.lower() for p in path.parts}
    name = path.name.lower()

    if parts & DROP_PARTS:
        return False

    if suffix in DROP_SUFFIXES:
        return False

    if suffix in KEEP_SUFFIXES:
        return True

    if suffix in {".html", ".htm"}:
        if name in KEEP_HTML_NAMES:
            return True
        if parts & KEEP_PARTS:
            return True

    return False

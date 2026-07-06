from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


DOMAIN_RULES = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "cpp", " c ",
        "linux kernel", "compiler", "programming", "arduino", "esp32",
        "android", "git", "github", "sql", "database", "postgres",
    ],
    "cybersecurity": [
        "kali", "hacking", "penetration", "pentest", "burp", "nmap",
        "xss", "xxe", "keylogger", "malware", "backdoor", "recon",
        "ethical hacking", "web application security",
    ],
    "religion": [
        "quran", "hadith", "dua", "deen", "sirah", "sirat", "sahabah",
        "tajweed", "arabic-english lexicon",
    ],
    "language": [
        "arabic", "grammar", "language", "dictionary", "lexicon",
        "pashto", "tajweed",
    ],
    "history": [
        "history", "caliphs", "afg-war", "war diary", "afghanistan",
        "marx", "engels",
    ],
    "physical_training": [
        "bodybuilding", "fitness", "muscle", "strength", "self-defense",
        "hand-to-hand", "pressure points",
    ],
    "aviation": [
        "aviation", "aircraft", "blackhawk", "uh-60", "faa", "maintenance",
    ],
}


TYPE_RULES = {
    "book": [
        ".pdf", ".epub", ".mobi", ".azw", ".azw3",
    ],
    "web_archive": [
        ".html", ".htm",
    ],
    "source_code": [
        ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".js", ".ts",
        ".sh", ".sql", ".rs", ".go",
    ],
    "image": [
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
    ],
    "audio": [
        ".mp3", ".wav", ".m4a", ".ogg", ".flac",
    ],
    "archive": [
        ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ],
    "structured_data": [
        ".json", ".xml", ".csv", ".sqlite", ".db",
    ],
    "offline_wiki": [
        ".zim",
    ],
}


@dataclass(frozen=True)
class Classification:
    discovered_file_id: int
    file_path: str
    knowledge_type: str
    domain: str
    subject: str
    confidence: float
    action: str
    reason: str


def normalize(text: str) -> str:
    return re.sub(r"[_\-.]+", " ", text.lower())


def detect_domain(path: str) -> tuple[str, float, str]:
    haystack = normalize(path)

    best_domain = "unknown"
    best_score = 0
    matched_terms: list[str] = []

    for domain, terms in DOMAIN_RULES.items():
        score = 0
        local_matches = []

        for term in terms:
            if term.lower() in haystack:
                score += 1
                local_matches.append(term)

        if score > best_score:
            best_score = score
            best_domain = domain
            matched_terms = local_matches

    if best_score == 0:
        return "unknown", 0.25, "no domain rule matched"

    confidence = min(0.95, 0.45 + (best_score * 0.12))
    return best_domain, confidence, "matched: " + ", ".join(matched_terms[:5])


def detect_type(extension: str, file_path: str, category: str) -> tuple[str, str]:
    ext = extension.lower()

    parts = set(Path(file_path).parts)

    if ".git" in parts:
        return "repository_artifact", "inside git repository"

    for knowledge_type, extensions in TYPE_RULES.items():
        if ext in extensions:
            return knowledge_type, f"extension {ext}"

    if category == "document":
        return "document", "discovery category document"

    if category == "source_code":
        return "source_code", "discovery category source_code"

    if category == "image":
        return "image", "discovery category image"

    if category == "archive":
        return "archive", "discovery category archive"

    return "unknown", "no type rule matched"


def detect_subject(file_path: str, domain: str) -> str:
    p = normalize(file_path)

    subject_terms = [
        "python", "java", "javascript", "kali", "linux", "c++", "cpp",
        "compiler", "arduino", "esp32", "android", "sql", "quran",
        "hadith", "arabic", "history", "afghanistan", "self defense",
    ]

    for term in subject_terms:
        if term in p:
            return term

    return domain


def decide_action(
    knowledge_type: str,
    domain: str,
    status: str,
    file_path: str,
) -> tuple[str, str]:
    p = file_path.lower()

    deny_fragments = [
        "/.venv/",
        "/venv/",
        "/site-packages/",
        "/__pycache__/",
        "/.idea/",
        "/.git/",
        "/node_modules/",
    ]

    if any(fragment in p for fragment in deny_fragments):
        return "ignore", "runtime, cache, IDE, dependency, or repository metadata"

    if status == "ignored":
        return "ignore", "already ignored during discovery"

    if knowledge_type in {"book", "document", "offline_wiki", "web_archive"}:
        return "candidate", "supported knowledge-bearing document"

    if knowledge_type == "source_code":
        return "review", "source code should be grouped into project/repository objects first"

    if knowledge_type in {"image", "audio", "archive", "structured_data"}:
        return "review", "requires specialized handling before assimilation"

    if domain == "unknown":
        return "review", "unknown domain"

    return "review", "needs human or future model review"


def classify_row(row: sqlite3.Row) -> Classification:
    file_id = row["id"]
    file_path = row["file_path"]
    extension = row["extension"] or ""
    category = row["category"]
    status = row["status"]

    knowledge_type, type_reason = detect_type(extension, file_path, category)
    domain, confidence, domain_reason = detect_domain(file_path)
    subject = detect_subject(file_path, domain)
    action, action_reason = decide_action(knowledge_type, domain, status, file_path)

    reason = f"{type_reason}; {domain_reason}; {action_reason}"

    return Classification(
        discovered_file_id=file_id,
        file_path=file_path,
        knowledge_type=knowledge_type,
        domain=domain,
        subject=subject,
        confidence=confidence,
        action=action,
        reason=reason,
    )


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discovered_file_id INTEGER NOT NULL UNIQUE,
            file_path TEXT NOT NULL UNIQUE,
            knowledge_type TEXT NOT NULL,
            domain TEXT NOT NULL,
            subject TEXT NOT NULL,
            confidence REAL NOT NULL,
            action TEXT NOT NULL,
            reason TEXT NOT NULL,
            classified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(discovered_file_id) REFERENCES discovered_files(id)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_classifications_type
        ON knowledge_classifications(knowledge_type)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_classifications_domain
        ON knowledge_classifications(domain)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_classifications_action
        ON knowledge_classifications(action)
        """
    )

    conn.commit()


def save_classification(conn: sqlite3.Connection, item: Classification) -> None:
    conn.execute(
        """
        INSERT INTO knowledge_classifications (
            discovered_file_id,
            file_path,
            knowledge_type,
            domain,
            subject,
            confidence,
            action,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(discovered_file_id) DO UPDATE SET
            file_path = excluded.file_path,
            knowledge_type = excluded.knowledge_type,
            domain = excluded.domain,
            subject = excluded.subject,
            confidence = excluded.confidence,
            action = excluded.action,
            reason = excluded.reason,
            classified_at = CURRENT_TIMESTAMP
        """,
        (
            item.discovered_file_id,
            item.file_path,
            item.knowledge_type,
            item.domain,
            item.subject,
            item.confidence,
            item.action,
            item.reason,
        ),
    )


def classify_discovered(
    db_path: str,
    root_filter: str | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    db = Path(db_path).expanduser().resolve()

    counts: dict[str, int] = {
        "seen": 0,
        "classified": 0,
        "errors": 0,
    }

    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        init_db(conn)

        sql = """
            SELECT id, file_path, extension, category, status
            FROM discovered_files
        """
        params: list[str] = []

        if root_filter:
            sql += " WHERE file_path LIKE ?"
            params.append(f"%{root_filter}%")

        sql += " ORDER BY id"

        if limit is not None:
            sql += " LIMIT ?"
            params.append(str(limit))

        rows = conn.execute(sql, params)

        for row in rows:
            counts["seen"] += 1

            try:
                item = classify_row(row)
                save_classification(conn, item)
                counts["classified"] += 1
                counts[item.action] = counts.get(item.action, 0) + 1
                counts[item.domain] = counts.get(item.domain, 0) + 1
            except Exception as exc:
                counts["errors"] += 1
                print(f"[WARN] Classification failed for {row['file_path']}: {exc}")

            if counts["seen"] % 1000 == 0:
                conn.commit()
                print(
                    f"[INFO] seen={counts['seen']} "
                    f"classified={counts['classified']} "
                    f"errors={counts['errors']}"
                )

        conn.commit()

    return counts

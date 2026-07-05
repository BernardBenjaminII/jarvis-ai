from __future__ import annotations


SUBJECT_RULES: dict[str, list[str]] = {
    "programming": [
        "programming", "python", "java", "c++", "cpp", " c ", "cmake",
        "compiler", "algorithm", "code", "software", "database", "sql",
        "linux", "bash", "rust", "javascript",
    ],
    "security": [
        "hacking", "security", "cyber", "pentest", "malware", "exploit",
        "vulnerability", "osint", "recon", "metasploit", "kali",
    ],
    "religion": [
        "deen", "quran", "islam", "hadith", "sunnah", "fiqh", "tafsir",
        "muslim", "allah", "prophet",
    ],
    "history": [
        "history", "war", "diary", "afghanistan", "afg", "military",
        "conflict", "archive",
    ],
    "aviation": [
        "aviation", "aircraft", "blackhawk", "uh 60", "uh-60", "faa",
        "maintenance", "helicopter",
    ],
    "academic": [
        "school", "course", "assignment", "project", "homework", "lecture",
        "exam", "university", "college",
    ],
}


def classify_subject(*texts: str | None) -> tuple[str | None, float, str]:
    haystack = " ".join(t or "" for t in texts).lower()

    scores: dict[str, int] = {}

    for subject, keywords in SUBJECT_RULES.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score:
            scores[subject] = score

    if not scores:
        return None, 0.0, "no subject rule matched"

    subject = max(scores, key=scores.get)
    score = scores[subject]
    confidence = min(0.95, 0.45 + (score * 0.10))

    return subject, confidence, f"matched {score} {subject} keyword(s)"

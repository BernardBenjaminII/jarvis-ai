from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from core.knowledge_catalog.paths import CATALOG_DB
from core.knowledge_graph.ontology import load_ontology


DEFAULT_REPORT_DIR = Path("knowledge/reports")


@dataclass
class SubjectCoverage:
    domain: str
    discipline: str
    subject: str
    file_count: int
    status: str
    score: int


def status_from_count(count: int) -> tuple[str, int]:
    if count == 0:
        return "missing", 0
    if count <= 2:
        return "weak", 25
    if count <= 9:
        return "developing", 60
    return "strong", 100


def iter_subjects() -> list[tuple[str, str, str]]:
    ontology = load_ontology()
    domains = ontology.domains.get("domains", {})

    subjects: list[tuple[str, str, str]] = []

    for domain_name, domain_body in domains.items():
        disciplines = (domain_body or {}).get("disciplines", {})

        for discipline_name, discipline_body in disciplines.items():
            discipline_body = discipline_body or {}
            subject_map = discipline_body.get("subjects", {}) or {}

            for subject_name in subject_map.keys():
                subjects.append((domain_name, discipline_name, subject_name))

    return subjects


def load_subject_counts() -> dict[str, int]:
    if not CATALOG_DB.exists():
        return {}

    with sqlite3.connect(CATALOG_DB) as conn:
        rows = conn.execute(
            """
            SELECT subject, COUNT(DISTINCT file_path) AS count
            FROM document_subjects
            GROUP BY subject
            """
        ).fetchall()

    return {subject: count for subject, count in rows}


def analyze_gaps() -> list[SubjectCoverage]:
    rows: list[SubjectCoverage] = []
    subject_counts = load_subject_counts()

    print(f"[Gap Analysis] Reading semantic catalog: {CATALOG_DB}")
    print(f"[Gap Analysis] Loaded {len(subject_counts)} mapped subjects")

    for domain, discipline, subject in iter_subjects():
        count = subject_counts.get(subject, 0)
        status, score = status_from_count(count)

        rows.append(
            SubjectCoverage(
                domain=domain,
                discipline=discipline,
                subject=subject,
                file_count=count,
                status=status,
                score=score,
            )
        )

    rows.sort(key=lambda r: (r.score, r.domain, r.discipline, r.subject))
    return rows


def summarize(rows: list[SubjectCoverage]) -> dict:
    total = len(rows)
    avg = sum(r.score for r in rows) / total if total else 0

    return {
        "total_subjects": total,
        "average_score": avg,
        "missing": sum(1 for r in rows if r.status == "missing"),
        "weak": sum(1 for r in rows if r.status == "weak"),
        "developing": sum(1 for r in rows if r.status == "developing"),
        "strong": sum(1 for r in rows if r.status == "strong"),
    }


def write_reports(
    rows: list[SubjectCoverage],
    report_dir: Path = DEFAULT_REPORT_DIR,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "gap_analysis.json"
    txt_path = report_dir / "gap_analysis.txt"

    payload = {
        "summary": summarize(rows),
        "subjects": [asdict(r) for r in rows],
    }

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = []
    lines.append("JARVIS Gap Analysis Report")
    lines.append("=" * 60)
    lines.append("")

    summary = payload["summary"]
    lines.append(f"Subjects analyzed: {summary['total_subjects']}")
    lines.append(f"Average score:     {summary['average_score']:.1f}")
    lines.append(f"Missing:           {summary['missing']}")
    lines.append(f"Weak:              {summary['weak']}")
    lines.append(f"Developing:        {summary['developing']}")
    lines.append(f"Strong:            {summary['strong']}")
    lines.append("")

    lines.append("Priority Gaps")
    lines.append("-" * 60)

    for row in rows:
        if row.status in {"missing", "weak"}:
            lines.append(
                f"{row.status.upper():<10} "
                f"{row.domain}/{row.discipline}/{row.subject} "
                f"files={row.file_count}"
            )

    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, txt_path

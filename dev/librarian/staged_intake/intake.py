from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from core.knowledge_catalog.assimilation.engine import assimilate_file, migrate


STAGED_ROOT = Path("/media/abdullah/JARVISDATA/Knowledge/Xfer_Staged_Files")
KNOWLEDGE_ROOT = Path("/media/abdullah/JARVISDATA/Knowledge")
INCOMING_ROOT = KNOWLEDGE_ROOT / "incoming"

SUPPORTED = {
    ".pdf", ".epub", ".txt", ".md", ".html", ".htm", ".doc", ".docx", ".png", ".jpg", ".jpeg"
}

IGNORE = {
    "thumbs.db", ".ds_store"
}

RISK_TERMS = [
    "al qaeda",
    "terrorist",
    "full-auto conversion",
    "select fire",
    "guerrilla warfare",
    "jihad",
    "nightingale",
    "mein kampf",
    "ultimate sniper",
    "dragunov",
]

ROUTES = [
    ("review_development", ["programming", "python", "c++", "java", "android", "linux kernel", "github", "project"]),
    ("review_cybersecurity", ["ethical hacking", "kali", "penetration", "hacking", "advanced penetration"]),
    ("review_religion", ["quran", "hadith", "tafsir", "islam", "salah", "hajj", "prophet", "deen", "seerah"]),
    ("review_languages", ["arabic", "pashto", "grammar", "dictionary", "language"]),
    ("review_history", ["history", "commission report", "afghanistan", "crs report"]),
    ("review_philosophy", ["plato", "aristotle", "nietzsche", "kant", "descartes", "marx", "rawls", "philosophy"]),
    ("review_education", ["ged", "study guide", "worksheet"]),
]


@dataclass
class IntakeDecision:
    source_path: Path
    action: str
    route: str | None
    reason: str
    dest_path: Path | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def text_for_path(path: Path) -> str:
    rel = str(path.relative_to(STAGED_ROOT)).lower()
    return rel.replace("_", " ").replace("-", " ")


def is_risky(path: Path) -> bool:
    text = text_for_path(path)
    return any(term in text for term in RISK_TERMS)


def choose_route(path: Path) -> tuple[str | None, str]:
    text = text_for_path(path)

    for route, terms in ROUTES:
        for term in terms:
            if term in text:
                return route, f"matched term: {term}"

    return None, "no route matched"


def safe_dest_path(route: str, source: Path) -> Path:
    rel = source.relative_to(STAGED_ROOT)
    dest = INCOMING_ROOT / route / rel

    if not dest.exists():
        return dest

    digest = sha256_file(source)[:12]
    return dest.with_name(f"{dest.stem}_{digest}{dest.suffix}")


def decide(path: Path) -> IntakeDecision:
    if not path.is_file():
        return IntakeDecision(path, "skip", None, "not a file")

    if path.name.lower() in IGNORE:
        return IntakeDecision(path, "skip", None, "ignored system file")

    if path.suffix.lower() not in SUPPORTED:
        return IntakeDecision(path, "skip", None, f"unsupported extension: {path.suffix}")

    if is_risky(path):
        return IntakeDecision(path, "quarantine_in_place", None, "risk term detected; leave staged for manual review")

    route, reason = choose_route(path)

    if not route:
        return IntakeDecision(path, "leave_unclassified", None, reason)

    dest = safe_dest_path(route, path)
    return IntakeDecision(path, "copy_and_assimilate", route, reason, dest)


def run_intake(dry_run: bool = True) -> list[IntakeDecision]:
    decisions: list[IntakeDecision] = []

    migrate()

    for path in sorted(STAGED_ROOT.rglob("*")):
        if not path.is_file():
            continue

        decision = decide(path)
        decisions.append(decision)

        if dry_run:
            continue

        if decision.action == "copy_and_assimilate" and decision.dest_path:
            decision.dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(decision.source_path, decision.dest_path)
            assimilate_file(decision.dest_path)

    return decisions


def write_report(decisions: list[IntakeDecision]) -> Path:
    report_dir = KNOWLEDGE_ROOT / ".jarvis" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "staged_intake_report.csv"

    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["action", "route", "reason", "source_path", "dest_path"],
        )
        writer.writeheader()

        for d in decisions:
            writer.writerow(
                {
                    "action": d.action,
                    "route": d.route or "",
                    "reason": d.reason,
                    "source_path": str(d.source_path),
                    "dest_path": str(d.dest_path or ""),
                }
            )

    return report_path


def print_summary(decisions: list[IntakeDecision]) -> None:
    counts = {}

    for d in decisions:
        counts[d.action] = counts.get(d.action, 0) + 1

    print("=" * 70)
    print("JARVIS STAGED INTAKE")
    print("=" * 70)

    for action, count in sorted(counts.items()):
        print(f"{action:<24} {count}")

    print()

    print("Routes:")
    route_counts = {}

    for d in decisions:
        if d.route:
            route_counts[d.route] = route_counts.get(d.route, 0) + 1

    for route, count in sorted(route_counts.items()):
        print(f"{route:<24} {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS staged knowledge intake")
    parser.add_argument("--apply", action="store_true", help="copy and assimilate approved files")
    args = parser.parse_args()

    decisions = run_intake(dry_run=not args.apply)
    report = write_report(decisions)
    print_summary(decisions)

    print()
    print(f"[OK] Report: {report}")

    if not args.apply:
        print("[DRY RUN] No files copied. Re-run with --apply to execute.")


if __name__ == "__main__":
    main()

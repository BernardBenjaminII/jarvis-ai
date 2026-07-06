from __future__ import annotations


def render_report(report: dict) -> str:
    lines: list[str] = []

    lines.append("JARVIS Knowledge Engine Doctor")
    lines.append("=" * 32)
    lines.append("")
    lines.append(f"Health score: {report.get('health_score', 0)}%")
    lines.append("")

    lines.append("Tables")
    lines.append("-" * 6)
    for table, ok in report.get("tables", {}).items():
        lines.append(f"{'PASS' if ok else 'FAIL'}  {table}")
    lines.append("")

    lines.append("Counts")
    lines.append("-" * 6)
    for key, value in sorted(report.get("counts", {}).items()):
        lines.append(f"{key}: {value}")
    lines.append("")

    lines.append("States")
    lines.append("-" * 6)
    for group, rows in report.get("states", {}).items():
        lines.append(f"[{group}]")
        for name, count in rows:
            lines.append(f"  {name}: {count}")
        lines.append("")

    lines.append("FAISS")
    lines.append("-" * 5)
    for key, value in report.get("faiss", {}).items():
        lines.append(f"{key}: {value}")
    lines.append("")

    lines.append("Issues")
    lines.append("-" * 6)
    issues = report.get("issues", [])
    if issues:
        for issue in issues:
            lines.append(f"FAIL  {issue}")
    else:
        lines.append("PASS  No critical issues found")
    lines.append("")

    lines.append("Warnings")
    lines.append("-" * 8)
    warnings = report.get("warnings", [])
    if warnings:
        for warning in warnings:
            lines.append(f"WARN  {warning}")
    else:
        lines.append("PASS  No warnings")
    lines.append("")

    return "\n".join(lines)

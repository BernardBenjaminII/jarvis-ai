#!/usr/bin/env python3
"""Non-destructive JARVIS Executive Integration audit."""

from __future__ import annotations

import ast
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

SUBSYSTEMS = {
    "executive": ["core/executive", "core/operations"],
    "capabilities": ["core/capabilities"],
    "knowledge": ["core/knowledge_catalog", "core/knowledge_graph", "knowledge_engine"],
    "reasoning": ["core/reasoning", "core/cognition", "core/representation"],
    "acquisition": ["core/acquisition", "knowledge_engine"],
    "runtime": ["core/bootstrap", "core/runtime"],
    "timeline": ["core/timeline", "core/executive"],
}

ROUTE_ROOTS = [Path("core/src/routes"), Path("api"), Path("server"), Path("backend")]
UI_ROOTS = [Path("ui"), Path("frontend"), Path("web"), Path("client"), Path("mission_control")]

PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.I),
    re.compile(r"\bFIXME\b", re.I),
    re.compile(r"\bmock\b", re.I),
    re.compile(r"\bplaceholder\b", re.I),
    re.compile(r"return\s+\{\s*\}"),
    re.compile(r"return\s+\[\s*\]"),
    re.compile(r'"status"\s*:\s*"ok"', re.I),
]

ROUTE_DECORATOR = re.compile(r"@\w+\.(get|post|put|patch|delete)\(\s*[rubf]*[\"']([^\"']+)")


@dataclass
class Finding:
    subsystem: str
    packages_present: list[str]
    route_files: list[str]
    ui_files: list[str]
    capability_files: list[str]
    test_files: list[str]
    verification_files: list[str]
    placeholder_hits: list[str]
    classification: str


def existing_paths(candidates: Iterable[str]) -> list[str]:
    return [p for p in candidates if (ROOT / p).exists()]


def collect_files(roots: Iterable[Path], suffixes: tuple[str, ...]) -> list[Path]:
    results: list[Path] = []
    for rel in roots:
        base = ROOT / rel
        if not base.exists():
            continue
        if base.is_file() and base.suffix in suffixes:
            results.append(base)
            continue
        results.extend(p for p in base.rglob("*") if p.is_file() and p.suffix in suffixes)
    return sorted(set(results))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def route_files_for(term: str, route_files: list[Path]) -> list[str]:
    found = []
    for path in route_files:
        body = text(path).lower()
        if term.lower() in body or term.lower() in path.stem.lower():
            found.append(rel(path))
    return found


def ui_files_for(term: str, ui_files: list[Path]) -> list[str]:
    aliases = {
        "executive": ["executive", "mission", "commander", "sitrep"],
        "capabilities": ["capability", "capabilities"],
        "knowledge": ["knowledge", "catalog", "coverage", "research queue"],
        "reasoning": ["reasoning", "hypothesis", "evidence"],
        "acquisition": ["acquisition", "ingest", "download"],
        "runtime": ["runtime", "model", "service", "health"],
        "timeline": ["timeline", "journal", "activity"],
    }
    needles = aliases.get(term, [term])
    found = []
    for path in ui_files:
        body = text(path).lower()
        searchable = body + " " + path.name.lower()
        if any(n in searchable for n in needles):
            found.append(rel(path))
    return found[:100]


def placeholder_hits(paths: list[Path], term: str) -> list[str]:
    hits = []
    for path in paths:
        body = text(path)
        if term.lower() not in (body + path.name).lower():
            continue
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(body):
                hits.append(f"{rel(path)} :: {pattern.pattern}")
                break
    return hits[:100]


def classify(packages: list[str], routes: list[str], ui: list[str], placeholders: list[str]) -> str:
    if ui and placeholders:
        return "ui_placeholder"
    if packages and routes and ui:
        return "fully_integrated_candidate"
    if packages and routes:
        return "api_only"
    if packages:
        return "backend_only"
    if routes or ui:
        return "unknown"
    return "unavailable"


def main() -> int:
    route_files = collect_files(ROUTE_ROOTS, (".py",))
    ui_files = collect_files(UI_ROOTS, (".ts", ".tsx", ".js", ".jsx", ".vue", ".html"))
    capability_files = collect_files([Path("core/capabilities")], (".py", ".yaml", ".yml", ".json"))
    test_files = collect_files([Path("tests")], (".py",))
    verification_files = collect_files([Path("dev"), Path("dev/verification")], (".py", ".sh"))

    findings: list[Finding] = []
    for subsystem, package_candidates in SUBSYSTEMS.items():
        packages = existing_paths(package_candidates)
        routes = route_files_for(subsystem, route_files)
        ui = ui_files_for(subsystem, ui_files)
        caps = [rel(p) for p in capability_files if subsystem in (text(p) + p.name).lower()]
        tests = [rel(p) for p in test_files if subsystem in (text(p) + p.name).lower()]
        verifies = [rel(p) for p in verification_files if subsystem in (text(p) + p.name).lower()]
        placeholders = placeholder_hits(route_files + ui_files, subsystem)
        findings.append(Finding(
            subsystem=subsystem,
            packages_present=packages,
            route_files=routes,
            ui_files=ui,
            capability_files=caps,
            test_files=tests,
            verification_files=verifies,
            placeholder_hits=placeholders,
            classification=classify(packages, routes, ui, placeholders),
        ))

    report_dir = ROOT / "docs/audits"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "executive_integration_audit.json"
    md_path = report_dir / "executive_integration_audit.md"
    csv_path = report_dir / "executive_integration_matrix.csv"

    payload = {
        "root": str(ROOT),
        "summary": {
            "subsystems": len(findings),
            "route_files": len(route_files),
            "ui_files": len(ui_files),
            "capability_files": len(capability_files),
            "test_files": len(test_files),
            "verification_files": len(verification_files),
        },
        "findings": [asdict(f) for f in findings],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "subsystem", "classification", "packages", "routes", "ui_files",
            "capability_files", "tests", "verification_files", "placeholder_hits"
        ])
        for f in findings:
            writer.writerow([
                f.subsystem, f.classification, len(f.packages_present),
                len(f.route_files), len(f.ui_files), len(f.capability_files),
                len(f.test_files), len(f.verification_files), len(f.placeholder_hits)
            ])

    lines = [
        "# Executive Integration Audit",
        "",
        f"**Repository:** `{ROOT}`",
        "",
        "## Summary",
        "",
        f"- Subsystems audited: {len(findings)}",
        f"- Route files discovered: {len(route_files)}",
        f"- UI files discovered: {len(ui_files)}",
        f"- Capability files discovered: {len(capability_files)}",
        f"- Test files discovered: {len(test_files)}",
        f"- Verification files discovered: {len(verification_files)}",
        "",
        "## Matrix",
        "",
        "| Subsystem | Classification | Packages | Routes | UI | Capabilities | Tests | Verification | Placeholder hits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for f in findings:
        lines.append(
            f"| {f.subsystem} | {f.classification} | {len(f.packages_present)} | "
            f"{len(f.route_files)} | {len(f.ui_files)} | {len(f.capability_files)} | "
            f"{len(f.test_files)} | {len(f.verification_files)} | {len(f.placeholder_hits)} |"
        )

    lines += ["", "## Detailed findings", ""]
    for f in findings:
        lines += [
            f"### {f.subsystem}",
            "",
            f"**Classification:** `{f.classification}`",
            "",
            f"**Packages:** {', '.join(f.packages_present) or 'None detected'}",
            "",
            f"**Routes:** {', '.join(f.route_files) or 'None detected'}",
            "",
            f"**UI files:** {', '.join(f.ui_files[:20]) or 'None detected'}",
            "",
            f"**Capability files:** {', '.join(f.capability_files[:20]) or 'None detected'}",
            "",
            f"**Placeholder indicators:** {', '.join(f.placeholder_hits[:20]) or 'None detected'}",
            "",
        ]

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("=" * 72)
    print("JARVIS — EXECUTIVE INTEGRATION AUDIT")
    print("=" * 72)
    for f in findings:
        print(
            f"[{f.classification.upper():28}] {f.subsystem:14} "
            f"packages={len(f.packages_present):2} routes={len(f.route_files):2} "
            f"ui={len(f.ui_files):3} placeholders={len(f.placeholder_hits):2}"
        )
    print("-" * 72)
    print(f"Report: {md_path.relative_to(ROOT)}")
    print(f"JSON  : {json_path.relative_to(ROOT)}")
    print(f"CSV   : {csv_path.relative_to(ROOT)}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

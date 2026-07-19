from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class BaselineBuildError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BaselineBuildError(f"Missing required audit report: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BaselineBuildError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BaselineBuildError(f"Audit report must contain an object: {path}")
    return data


def collect_names(report: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for key in ("contracts", "classes", "services", "components"):
        items = report.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    names.add(item["name"])
    modules = report.get("modules")
    if isinstance(modules, dict):
        for module in modules.values():
            if not isinstance(module, dict):
                continue
            for key in ("classes", "contracts", "services", "components"):
                items = module.get(key)
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and isinstance(item.get("name"), str):
                            names.add(item["name"])
    return names


def validate_reports(a1: dict[str, Any], a2: dict[str, Any], a3: dict[str, Any]) -> None:
    requirements = (
        ("I-A1", {"EvidenceItem", "Hypothesis", "ReasoningRequest", "PlanningRecommendation", "ReasoningResult"}, collect_names(a1)),
        ("I-A2", {"ReasoningEngine"}, collect_names(a2)),
        ("I-A3", {"KnowledgeEvidenceAdapter", "KnowledgeReasoningPipeline"}, collect_names(a3)),
    )
    failures: list[str] = []
    for phase, required, observed in requirements:
        missing = sorted(required - observed)
        if missing:
            failures.append(f"{phase} missing: {', '.join(missing)}")
    if failures:
        raise BaselineBuildError("; ".join(failures))


def describe_report(root: Path, phase: str, path: Path, report: dict[str, Any]) -> dict[str, str]:
    return {
        "phase": phase,
        "path": str(path.relative_to(root)),
        "audit_id": str(report.get("audit_id", "")),
        "title": str(report.get("title", "")),
        "fingerprint": fingerprint(report),
    }

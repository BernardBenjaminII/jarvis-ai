from __future__ import annotations

from typing import Any

from .contracts import EngineeringReport
from .normalize import normalize_report


def report_to_dict(value: Any) -> dict:
    return normalize_report(value).to_dict()


def report_to_json(value: Any) -> str:
    return normalize_report(value).to_json()


def report_to_markdown(value: Any) -> str:
    return normalize_report(value).to_markdown()


def is_engineering_report(value: Any) -> bool:
    return isinstance(value, EngineeringReport)

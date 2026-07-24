"""
Canonical JARVIS master-verification runner.

Usage:

    python -m dev.verification.runner
    python -m dev.verification.runner --list
    python -m dev.verification.runner --only 6f3,6f4
    python -m dev.verification.runner --category services
    python -m dev.verification.runner --no-json
    python -m dev.verification.runner --json-out /tmp/report.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from dev.verification.models import (
    SuiteDefinition,
    SuiteResult,
    VerificationReport,
)
from dev.verification.registry import (
    VERIFICATION_SUITES,
    validate_registry,
)


FRAMEWORK_VERSION = "1.0"
DEFAULT_JSON_OUTPUT = Path(
    "/tmp/jarvis-verification/latest.json"
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_git(
    root: Path,
    *arguments: str,
) -> str | None:
    try:
        completed = subprocess.run(
            [
                "git",
                *arguments,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if completed.returncode != 0:
        return None

    return completed.stdout.strip() or None


def git_metadata(
    root: Path,
) -> tuple[str | None, str | None, bool | None]:
    commit = run_git(
        root,
        "rev-parse",
        "HEAD",
    )

    branch = run_git(
        root,
        "branch",
        "--show-current",
    )

    status = run_git(
        root,
        "status",
        "--porcelain",
    )

    dirty = (
        bool(status)
        if status is not None
        else None
    )

    return commit, branch, dirty


def select_suites(
    suites: Sequence[SuiteDefinition],
    *,
    only_ids: set[str] | None = None,
    categories: set[str] | None = None,
) -> tuple[SuiteDefinition, ...]:
    selected: list[SuiteDefinition] = []

    for suite in suites:
        if (
            only_ids is not None
            and suite.suite_id not in only_ids
        ):
            continue

        if (
            categories is not None
            and suite.category not in categories
        ):
            continue

        selected.append(suite)

    if only_ids is not None:
        known = {
            suite.suite_id
            for suite in suites
        }

        unknown = sorted(
            only_ids - known
        )

        if unknown:
            raise ValueError(
                "Unknown verification suite IDs: "
                + ", ".join(unknown)
            )

    return tuple(selected)


def execute_suite(
    suite: SuiteDefinition,
    *,
    root: Path,
    python_bin: str,
) -> SuiteResult:
    script = root / suite.script_path

    if not script.exists():
        status = (
            "missing"
            if suite.required
            else "skipped"
        )

        return SuiteResult(
            suite_id=suite.suite_id,
            name=suite.name,
            script_path=suite.script_path,
            required=suite.required,
            category=suite.category,
            status=status,
            return_code=None,
            elapsed_seconds=0.0,
            stdout="",
            stderr="",
            failure_reason=(
                "required verification script is missing"
                if suite.required
                else "optional verification script is missing"
            ),
        )

    if not script.is_file():
        return SuiteResult(
            suite_id=suite.suite_id,
            name=suite.name,
            script_path=suite.script_path,
            required=suite.required,
            category=suite.category,
            status="failed",
            return_code=None,
            elapsed_seconds=0.0,
            stdout="",
            stderr="",
            failure_reason=(
                "verification path is not a regular file"
            ),
        )

    environment = os.environ.copy()
    environment["PYTHON_BIN"] = python_bin

    started = time.perf_counter()

    try:
        completed = subprocess.run(
            [
                "bash",
                str(script),
            ],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        elapsed = time.perf_counter() - started

        return SuiteResult(
            suite_id=suite.suite_id,
            name=suite.name,
            script_path=suite.script_path,
            required=suite.required,
            category=suite.category,
            status="failed",
            return_code=None,
            elapsed_seconds=elapsed,
            stdout="",
            stderr="",
            failure_reason=(
                f"{type(exc).__name__}: {exc}"
            ),
        )

    elapsed = time.perf_counter() - started

    passed = completed.returncode == 0

    return SuiteResult(
        suite_id=suite.suite_id,
        name=suite.name,
        script_path=suite.script_path,
        required=suite.required,
        category=suite.category,
        status=(
            "passed"
            if passed
            else "failed"
        ),
        return_code=completed.returncode,
        elapsed_seconds=elapsed,
        stdout=completed.stdout,
        stderr=completed.stderr,
        failure_reason=(
            None
            if passed
            else (
                "verification script returned "
                f"exit code {completed.returncode}"
            )
        ),
    )


def build_report(
    *,
    root: Path,
    selected: Sequence[SuiteDefinition],
    results: Sequence[SuiteResult],
    started_at: str,
    completed_at: str,
    elapsed_seconds: float,
) -> VerificationReport:
    commit, branch, dirty = git_metadata(root)

    return VerificationReport(
        framework_version=FRAMEWORK_VERSION,
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=elapsed_seconds,
        repository_root=str(root),
        git_commit=commit,
        git_branch=branch,
        git_dirty=dirty,
        selected_suite_ids=tuple(
            suite.suite_id
            for suite in selected
        ),
        results=tuple(results),
    )


def write_json_report(
    report: VerificationReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            report.to_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(output_path)


def print_suite_header(
    suite: SuiteDefinition,
) -> None:
    print()
    print("-" * 70)
    print(
        f"Running {suite.script_path} "
        f"[{suite.suite_id}: {suite.category}]"
    )
    print("-" * 70)


def print_suite_result(
    result: SuiteResult,
) -> None:
    if result.stdout:
        print(
            result.stdout,
            end=(
                ""
                if result.stdout.endswith("\n")
                else "\n"
            ),
        )

    if result.stderr:
        print(
            result.stderr,
            file=sys.stderr,
            end=(
                ""
                if result.stderr.endswith("\n")
                else "\n"
            ),
        )

    label = result.status.upper()

    print(
        f"[{label}] {result.script_path} "
        f"({result.elapsed_seconds:.3f} sec)"
    )

    if result.failure_reason:
        print(
            f"Reason: {result.failure_reason}"
        )


def print_summary(
    report: VerificationReport,
    *,
    json_path: Path | None,
) -> None:
    print()
    print("=" * 70)
    print("MASTER VERIFICATION SUMMARY")
    print("=" * 70)
    print(
        f"Suites Executed: {report.suites_executed:13d}"
    )
    print(
        f"Suites Passed:   {report.suites_passed:13d}"
    )
    print(
        f"Suites Failed:   {report.suites_failed:13d}"
    )
    print(
        f"Suites Skipped:  {report.suites_skipped:13d}"
    )
    print(
        f"Suites Missing:  {report.suites_missing:13d}"
    )
    print(
        f"Elapsed Time:    {report.elapsed_seconds:12.3f} sec"
    )
    print()

    if report.git_commit:
        print(f"Git Commit   : {report.git_commit}")

    if report.git_branch:
        print(f"Git Branch   : {report.git_branch}")

    if report.git_dirty is not None:
        print(
            "Working Tree : "
            + (
                "DIRTY"
                if report.git_dirty
                else "CLEAN"
            )
        )

    if json_path is not None:
        print(f"JSON Report  : {json_path}")

    print()

    if report.passed:
        print("Overall Status : EXCELLENT")
        print()
        print("JARVIS Gen 2 verification PASSED.")
    else:
        print("Overall Status : FAILED")
        print()
        print(
            "One or more required verification suites failed."
        )


def list_suites(
    suites: Iterable[SuiteDefinition],
) -> None:
    print(
        "ID      REQUIRED  CATEGORY       SCRIPT"
    )
    print("-" * 78)

    for suite in suites:
        print(
            f"{suite.suite_id:<7} "
            f"{str(suite.required):<9} "
            f"{suite.category:<14} "
            f"{suite.script_path}"
        )


def parse_csv(
    values: Sequence[str] | None,
) -> set[str] | None:
    if not values:
        return None

    parsed: set[str] = set()

    for value in values:
        parsed.update(
            part.strip()
            for part in value.split(",")
            if part.strip()
        )

    return parsed or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the canonical JARVIS verification suite."
        )
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List registered suites without executing them.",
    )

    parser.add_argument(
        "--only",
        action="append",
        help=(
            "Run only selected suite IDs. "
            "May be repeated or comma-separated."
        ),
    )

    parser.add_argument(
        "--category",
        action="append",
        help=(
            "Run only selected suite categories. "
            "May be repeated or comma-separated."
        ),
    )

    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help=(
            "JSON report path. Default: "
            f"{DEFAULT_JSON_OUTPUT}"
        ),
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Do not create a JSON report.",
    )

    parser.add_argument(
        "--python-bin",
        default=os.environ.get(
            "PYTHON_BIN",
            sys.executable,
        ),
        help=(
            "Python interpreter supplied to phase scripts."
        ),
    )

    return parser


def main(
    arguments: Sequence[str] | None = None,
) -> int:
    validate_registry()

    parser = build_parser()
    args = parser.parse_args(arguments)

    if args.list:
        list_suites(VERIFICATION_SUITES)
        return 0

    try:
        selected = select_suites(
            VERIFICATION_SUITES,
            only_ids=parse_csv(args.only),
            categories=parse_csv(args.category),
        )
    except ValueError as exc:
        parser.error(str(exc))

    if not selected:
        parser.error(
            "No verification suites matched the selection"
        )

    root = repository_root()

    print()
    print("=" * 70)
    print("JARVIS GEN 2 — MASTER VERIFICATION FRAMEWORK")
    print("=" * 70)
    print(f"Framework Version: {FRAMEWORK_VERSION}")
    print(f"Repository Root  : {root}")
    print(f"Python Binary    : {args.python_bin}")

    started_at = utc_now()
    started = time.perf_counter()

    results: list[SuiteResult] = []

    for suite in selected:
        print_suite_header(suite)

        result = execute_suite(
            suite,
            root=root,
            python_bin=args.python_bin,
        )

        results.append(result)
        print_suite_result(result)

    elapsed = time.perf_counter() - started
    completed_at = utc_now()

    report = build_report(
        root=root,
        selected=selected,
        results=results,
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=elapsed,
    )

    json_path: Path | None = None

    if not args.no_json:
        json_path = args.json_out.expanduser()
        write_json_report(
            report,
            json_path,
        )

    print_summary(
        report,
        json_path=json_path,
    )

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

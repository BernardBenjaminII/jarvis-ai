"""
JARVIS safe-commit gate.

The gate never stages files automatically.

The developer must inspect and stage exactly one milestone before running it.

Default sequence:

1. Discover the repository root.
2. Reject merge, rebase, cherry-pick, or revert operations in progress.
3. Verify Git object and index health.
4. Require at least one staged file.
5. Reject unmerged paths.
6. Run staged whitespace checks.
7. Reject staged conflict markers.
8. Run an optional focused verification script.
9. Run the canonical Python master-verification framework.
10. Stop after verification when --dry-run is supplied.
11. Create one commit.
12. Push only when --push is explicitly supplied.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


CONFLICT_MARKER_PATTERN = re.compile(
    r"^(<<<<<<<(?: .*)?|=======|>>>>>>>.*)$"
)


class SafeCommitError(RuntimeError):
    """Raised when a safe-commit gate rejects the repository state."""


@dataclass(frozen=True)
class SafeCommitResult:
    """Immutable summary of one safe-commit execution."""

    repository_root: str
    staged_files: tuple[str, ...]
    focused_verification_ran: bool
    master_verification_ran: bool
    verification_report: str
    dry_run: bool
    committed: bool
    pushed: bool
    commit_hash: str | None


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run one command without shell expansion."""

    try:
        return subprocess.run(
            list(command),
            cwd=cwd,
            env=environment,
            capture_output=capture_output,
            text=True,
            check=False,
        )
    except OSError as exc:
        executable = command[0] if command else "<empty>"
        raise SafeCommitError(
            f"Unable to execute {executable!r}: {exc}"
        ) from exc


def require_success(
    completed: subprocess.CompletedProcess[str],
    *,
    description: str,
) -> None:
    """Raise SafeCommitError when a command fails."""

    if completed.returncode == 0:
        return

    details = "\n".join(
        value.strip()
        for value in (
            completed.stdout,
            completed.stderr,
        )
        if value and value.strip()
    )

    message = (
        f"{description} failed with exit code "
        f"{completed.returncode}"
    )

    if details:
        message += f":\n{details}"

    raise SafeCommitError(message)


def discover_repository_root(
    starting_path: Path,
) -> Path:
    """Return the active Git repository root."""

    completed = run_command(
        [
            "git",
            "rev-parse",
            "--show-toplevel",
        ],
        cwd=starting_path,
    )

    require_success(
        completed,
        description="Git repository discovery",
    )

    return Path(
        completed.stdout.strip()
    ).resolve()


def resolve_git_directory(
    repository_root: Path,
) -> Path:
    """Resolve the active .git metadata directory."""

    completed = run_command(
        [
            "git",
            "rev-parse",
            "--git-dir",
        ],
        cwd=repository_root,
    )

    require_success(
        completed,
        description="Git directory discovery",
    )

    git_directory = Path(
        completed.stdout.strip()
    )

    if not git_directory.is_absolute():
        git_directory = (
            repository_root
            / git_directory
        )

    return git_directory.resolve()


def verify_no_git_operation_in_progress(
    repository_root: Path,
) -> None:
    """Reject unfinished merge, rebase, cherry-pick, or revert work."""

    git_directory = resolve_git_directory(
        repository_root
    )

    markers = {
        "merge": git_directory / "MERGE_HEAD",
        "cherry-pick": git_directory / "CHERRY_PICK_HEAD",
        "revert": git_directory / "REVERT_HEAD",
        "rebase-apply": git_directory / "rebase-apply",
        "rebase-merge": git_directory / "rebase-merge",
    }

    active = [
        name
        for name, path in markers.items()
        if path.exists()
    ]

    if active:
        raise SafeCommitError(
            "Unfinished Git operation detected: "
            + ", ".join(active)
        )


def verify_repository_health(
    repository_root: Path,
) -> None:
    """
    Verify Git object and index health.

    Dangling objects are acceptable when git fsck exits successfully.
    """

    fsck = run_command(
        [
            "git",
            "fsck",
            "--full",
        ],
        cwd=repository_root,
    )

    require_success(
        fsck,
        description="Git object database verification",
    )

    index = run_command(
        [
            "git",
            "status",
            "--porcelain",
        ],
        cwd=repository_root,
    )

    require_success(
        index,
        description="Git index verification",
    )


def staged_files(
    repository_root: Path,
) -> tuple[str, ...]:
    """Return staged paths in deterministic order."""

    completed = run_command(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
        ],
        cwd=repository_root,
    )

    require_success(
        completed,
        description="Staged-file inventory",
    )

    files = tuple(
        sorted(
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        )
    )

    if not files:
        raise SafeCommitError(
            "No staged files. Review and stage one milestone first."
        )

    return files


def verify_no_unmerged_paths(
    repository_root: Path,
) -> None:
    """Reject unresolved merge entries."""

    completed = run_command(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=U",
        ],
        cwd=repository_root,
    )

    require_success(
        completed,
        description="Unmerged-path inspection",
    )

    paths = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    ]

    if paths:
        raise SafeCommitError(
            "Unmerged paths remain:\n"
            + "\n".join(paths)
        )


def verify_staged_diff(
    repository_root: Path,
) -> None:
    """Run Git's staged whitespace validation."""

    completed = run_command(
        [
            "git",
            "diff",
            "--cached",
            "--check",
        ],
        cwd=repository_root,
    )

    require_success(
        completed,
        description="Staged diff validation",
    )


def read_staged_text(
    repository_root: Path,
    path: str,
) -> str | None:
    """Read one staged blob as text, ignoring binary entries."""

    completed = run_command(
        [
            "git",
            "show",
            f":{path}",
        ],
        cwd=repository_root,
    )

    if completed.returncode != 0:
        return None

    raw = completed.stdout.encode(
        "utf-8",
        errors="surrogateescape",
    )

    if b"\x00" in raw:
        return None

    return raw.decode(
        "utf-8",
        errors="replace",
    )


def verify_no_staged_conflict_markers(
    repository_root: Path,
    files: Sequence[str],
) -> None:
    """Reject unresolved conflict markers in staged text."""

    violations: list[str] = []

    for path in files:
        text = read_staged_text(
            repository_root,
            path,
        )

        if text is None:
            continue

        for line_number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if CONFLICT_MARKER_PATTERN.match(line):
                violations.append(
                    f"{path}:{line_number}:{line}"
                )

    if violations:
        raise SafeCommitError(
            "Staged conflict markers detected:\n"
            + "\n".join(violations)
        )


def verification_environment(
    python_bin: str,
) -> dict[str, str]:
    """Build the environment passed to verification scripts."""

    environment = os.environ.copy()
    environment["PYTHON_BIN"] = python_bin
    return environment


def run_focused_verification(
    repository_root: Path,
    *,
    script_path: str,
    python_bin: str,
) -> None:
    """Run one focused phase wrapper."""

    script = (
        repository_root
        / script_path
    )

    if not script.exists():
        raise SafeCommitError(
            "Focused verification script does not exist: "
            f"{script_path}"
        )

    if not script.is_file():
        raise SafeCommitError(
            "Focused verification path is not a file: "
            f"{script_path}"
        )

    completed = run_command(
        [
            "bash",
            str(script),
        ],
        cwd=repository_root,
        environment=verification_environment(
            python_bin
        ),
        capture_output=False,
    )

    require_success(
        completed,
        description=(
            f"Focused verification {script_path}"
        ),
    )


def run_master_verification(
    repository_root: Path,
    *,
    python_bin: str,
    report_path: Path,
    command_override: Sequence[str] | None = None,
) -> None:
    """Run the canonical Python master-verification framework."""

    report_path = report_path.expanduser().resolve()

    if command_override is None:
        command = [
            python_bin,
            "-m",
            "dev.verification.runner",
            "--json-out",
            str(report_path),
        ]
    else:
        command = list(
            command_override
        )

    completed = run_command(
        command,
        cwd=repository_root,
        environment=verification_environment(
            python_bin
        ),
        capture_output=False,
    )

    require_success(
        completed,
        description="Master verification",
    )

    if command_override is None:
        if not report_path.exists():
            raise SafeCommitError(
                "Master verification passed but did not create "
                f"the JSON report: {report_path}"
            )

        if report_path.stat().st_size == 0:
            raise SafeCommitError(
                "Master verification created an empty JSON report: "
                f"{report_path}"
            )


def create_commit(
    repository_root: Path,
    *,
    message: str,
) -> str:
    """Create the reviewed milestone commit."""

    normalized_message = message.strip()

    if not normalized_message:
        raise SafeCommitError(
            "Commit message must not be empty"
        )

    completed = run_command(
        [
            "git",
            "commit",
            "-m",
            normalized_message,
        ],
        cwd=repository_root,
        capture_output=False,
    )

    require_success(
        completed,
        description="Git commit",
    )

    revision = run_command(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=repository_root,
    )

    require_success(
        revision,
        description="Committed revision lookup",
    )

    return revision.stdout.strip()


def push_commit(
    repository_root: Path,
) -> None:
    """Push the active branch to its configured upstream."""

    completed = run_command(
        [
            "git",
            "push",
        ],
        cwd=repository_root,
        capture_output=False,
    )

    require_success(
        completed,
        description="Git push",
    )


def run_safe_commit(
    *,
    repository_root: Path,
    message: str,
    focused_script: str | None = None,
    python_bin: str = sys.executable,
    report_path: Path = Path(
        "/tmp/jarvis-verification/pre-commit.json"
    ),
    dry_run: bool = False,
    push: bool = False,
    master_command_override: Sequence[str] | None = None,
) -> SafeCommitResult:
    """Execute the complete safe-commit workflow."""

    root = repository_root.resolve()
    resolved_report = report_path.expanduser().resolve()

    verify_no_git_operation_in_progress(
        root
    )
    verify_repository_health(
        root
    )

    files = staged_files(
        root
    )

    verify_no_unmerged_paths(
        root
    )
    verify_staged_diff(
        root
    )
    verify_no_staged_conflict_markers(
        root,
        files,
    )

    focused_ran = False

    if focused_script is not None:
        run_focused_verification(
            root,
            script_path=focused_script,
            python_bin=python_bin,
        )
        focused_ran = True

    run_master_verification(
        root,
        python_bin=python_bin,
        report_path=resolved_report,
        command_override=master_command_override,
    )

    if dry_run:
        return SafeCommitResult(
            repository_root=str(root),
            staged_files=files,
            focused_verification_ran=focused_ran,
            master_verification_ran=True,
            verification_report=str(
                resolved_report
            ),
            dry_run=True,
            committed=False,
            pushed=False,
            commit_hash=None,
        )

    commit_hash = create_commit(
        root,
        message=message,
    )

    pushed = False

    if push:
        push_commit(
            root
        )
        pushed = True

    return SafeCommitResult(
        repository_root=str(root),
        staged_files=files,
        focused_verification_ran=focused_ran,
        master_verification_ran=True,
        verification_report=str(
            resolved_report
        ),
        dry_run=False,
        committed=True,
        pushed=pushed,
        commit_hash=commit_hash,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the safe-commit command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Verify, commit, and optionally push one staged "
            "JARVIS milestone."
        )
    )

    parser.add_argument(
        "--message",
        required=True,
        help="Commit message for the staged milestone.",
    )

    parser.add_argument(
        "--focused-script",
        help=(
            "Focused phase verification wrapper, such as "
            "dev/verify_phase_6f7.sh."
        ),
    )

    parser.add_argument(
        "--python-bin",
        default=os.environ.get(
            "PYTHON_BIN",
            sys.executable,
        ),
        help="Python interpreter used by verification.",
    )

    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path(
            "/tmp/jarvis-verification/pre-commit.json"
        ),
        help="Master-verification JSON report path.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Run every gate without committing or pushing."
        ),
    )

    parser.add_argument(
        "--push",
        action="store_true",
        help="Push after a successful commit.",
    )

    return parser


def main(
    arguments: Sequence[str] | None = None,
) -> int:
    """Run the safe-commit command-line interface."""

    parser = build_parser()
    args = parser.parse_args(
        arguments
    )

    try:
        root = discover_repository_root(
            Path.cwd()
        )

        result = run_safe_commit(
            repository_root=root,
            message=args.message,
            focused_script=args.focused_script,
            python_bin=args.python_bin,
            report_path=args.report_path,
            dry_run=args.dry_run,
            push=args.push,
        )
    except SafeCommitError as exc:
        print(
            f"[FAIL] {exc}",
            file=sys.stderr,
        )
        return 1

    print()
    print("=" * 70)
    print("JARVIS SAFE-COMMIT SUMMARY")
    print("=" * 70)
    print(f"Repository : {result.repository_root}")
    print(f"Staged     : {len(result.staged_files)} files")

    for path in result.staged_files:
        print(f"  - {path}")

    print(
        "Focused    : "
        + (
            "PASSED"
            if result.focused_verification_ran
            else "NOT REQUESTED"
        )
    )
    print("Master     : PASSED")
    print(f"Report     : {result.verification_report}")
    print(
        "Mode       : "
        + (
            "DRY RUN"
            if result.dry_run
            else "COMMIT"
        )
    )

    if result.commit_hash:
        print(f"Commit     : {result.commit_hash}")

    print(
        "Push       : "
        + (
            "COMPLETED"
            if result.pushed
            else "NOT REQUESTED"
        )
    )
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

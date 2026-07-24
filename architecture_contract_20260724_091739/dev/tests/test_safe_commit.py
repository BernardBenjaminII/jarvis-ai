"""
JARVIS Gen 2 Phase VI-F7 safe-commit contracts.

All Git operations occur inside temporary repositories.

No commit or push is performed against the real JARVIS repository.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

from dev.release.safe_commit import (
    SafeCommitError,
    SafeCommitResult,
    run_safe_commit,
)


def git(
    root: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run Git inside one temporary repository."""

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

    if (
        check
        and completed.returncode != 0
    ):
        raise AssertionError(
            f"git {' '.join(arguments)} failed:\n"
            f"{completed.stdout}\n"
            f"{completed.stderr}"
        )

    return completed


def create_repository(
    root: Path,
) -> None:
    """Create a temporary repository with one initial commit."""

    git(
        root,
        "init",
    )

    git(
        root,
        "config",
        "user.name",
        "JARVIS Verification Test",
    )

    git(
        root,
        "config",
        "user.email",
        "jarvis-test@example.invalid",
    )

    (root / "README.md").write_text(
        "# Temporary JARVIS Test Repository\n",
        encoding="utf-8",
    )

    git(
        root,
        "add",
        "README.md",
    )

    git(
        root,
        "commit",
        "-m",
        "Initial commit",
    )


def create_verifier(
    path: Path,
    *,
    exit_code: int,
) -> None:
    """Create a temporary verification shell script."""

    path.write_text(
        "#!/usr/bin/env bash\n"
        "set -Eeuo pipefail\n"
        f'echo "temporary verifier exit {exit_code}"\n'
        f"exit {exit_code}\n",
        encoding="utf-8",
    )

    path.chmod(
        0o755
    )


def stage_text_file(
    root: Path,
    *,
    relative_path: str,
    content: str,
) -> None:
    """Create and stage one temporary text file."""

    path = root / relative_path

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    git(
        root,
        "add",
        relative_path,
    )


def reset_and_remove(
    root: Path,
    relative_path: str,
) -> None:
    """Unstage and remove a temporary working-tree file."""

    git(
        root,
        "reset",
        "HEAD",
        relative_path,
        check=False,
    )

    path = root / relative_path

    if path.exists():
        path.unlink()


def assert_frozen(
    instance: object,
    attribute_name: str,
    replacement: object,
) -> None:
    """Verify immutable result models."""

    try:
        setattr(
            instance,
            attribute_name,
            replacement,
        )
    except FrozenInstanceError:
        return

    raise AssertionError(
        f"{type(instance).__name__} must remain immutable"
    )


def verify_dry_run_success(
    root: Path,
    passing_verifier: Path,
) -> None:
    stage_text_file(
        root,
        relative_path="dry-run.txt",
        content="reviewed staged content\n",
    )

    before = git(
        root,
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    result = run_safe_commit(
        repository_root=root,
        message="Dry-run rehearsal",
        dry_run=True,
        master_command_override=[
            "bash",
            str(passing_verifier),
        ],
    )

    after = git(
        root,
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    assert isinstance(
        result,
        SafeCommitResult,
    )

    assert result.dry_run is True
    assert result.committed is False
    assert result.pushed is False
    assert result.commit_hash is None
    assert result.master_verification_ran is True
    assert result.staged_files == (
        "dry-run.txt",
    )
    assert before == after

    assert_frozen(
        result,
        "committed",
        True,
    )

    reset_and_remove(
        root,
        "dry-run.txt",
    )


def verify_real_commit_success(
    root: Path,
    passing_verifier: Path,
) -> None:
    stage_text_file(
        root,
        relative_path="committed.txt",
        content="safe committed content\n",
    )

    before = git(
        root,
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    result = run_safe_commit(
        repository_root=root,
        message="Safe commit contract test",
        dry_run=False,
        push=False,
        master_command_override=[
            "bash",
            str(passing_verifier),
        ],
    )

    after = git(
        root,
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    assert result.committed is True
    assert result.pushed is False
    assert result.commit_hash == after
    assert before != after

    subject = git(
        root,
        "log",
        "-1",
        "--pretty=%s",
    ).stdout.strip()

    assert subject == (
        "Safe commit contract test"
    )


def verify_empty_stage_rejected(
    root: Path,
    passing_verifier: Path,
) -> None:
    try:
        run_safe_commit(
            repository_root=root,
            message="Must fail",
            dry_run=True,
            master_command_override=[
                "bash",
                str(passing_verifier),
            ],
        )
    except SafeCommitError as exc:
        assert "No staged files" in str(exc)
    else:
        raise AssertionError(
            "Safe commit accepted an empty staged set"
        )


def verify_failed_verification_blocks_commit(
    root: Path,
    failing_verifier: Path,
) -> None:
    stage_text_file(
        root,
        relative_path="blocked.txt",
        content="must remain staged\n",
    )

    before = git(
        root,
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    try:
        run_safe_commit(
            repository_root=root,
            message="Must not commit",
            dry_run=False,
            master_command_override=[
                "bash",
                str(failing_verifier),
            ],
        )
    except SafeCommitError as exc:
        assert "Master verification" in str(exc)
    else:
        raise AssertionError(
            "Failed verification did not block commit"
        )

    after = git(
        root,
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    assert before == after

    staged = git(
        root,
        "diff",
        "--cached",
        "--name-only",
    ).stdout.splitlines()

    assert staged == [
        "blocked.txt",
    ]

    reset_and_remove(
        root,
        "blocked.txt",
    )


def verify_conflict_markers_rejected(
    root: Path,
    passing_verifier: Path,
) -> None:
    stage_text_file(
        root,
        relative_path="conflict.txt",
        content=(
            "<<<<<<< HEAD\n"
            "alpha\n"
            "=======\n"
            "bravo\n"
            ">>>>>>> branch\n"
        ),
    )

    try:
        run_safe_commit(
            repository_root=root,
            message="Must reject conflicts",
            dry_run=True,
            master_command_override=[
                "bash",
                str(passing_verifier),
            ],
        )
    except SafeCommitError as exc:
        message = str(exc).lower()

        assert (
            "conflict" in message
            or "diff validation" in message
        )
    else:
        raise AssertionError(
            "Conflict markers were accepted"
        )

    reset_and_remove(
        root,
        "conflict.txt",
    )


def verify_whitespace_errors_rejected(
    root: Path,
    passing_verifier: Path,
) -> None:
    stage_text_file(
        root,
        relative_path="whitespace.txt",
        content="trailing whitespace   \n",
    )

    try:
        run_safe_commit(
            repository_root=root,
            message="Must reject whitespace",
            dry_run=True,
            master_command_override=[
                "bash",
                str(passing_verifier),
            ],
        )
    except SafeCommitError as exc:
        assert "diff validation" in str(exc)
    else:
        raise AssertionError(
            "Whitespace errors were accepted"
        )

    reset_and_remove(
        root,
        "whitespace.txt",
    )


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="jarvis-safe-commit-"
    ) as temporary:
        root = Path(temporary)

        create_repository(
            root
        )

        passing_verifier = (
            root
            / "passing-verifier.sh"
        )

        failing_verifier = (
            root
            / "failing-verifier.sh"
        )

        create_verifier(
            passing_verifier,
            exit_code=0,
        )

        create_verifier(
            failing_verifier,
            exit_code=9,
        )

        verify_dry_run_success(
            root,
            passing_verifier,
        )

        verify_real_commit_success(
            root,
            passing_verifier,
        )

        verify_empty_stage_rejected(
            root,
            passing_verifier,
        )

        verify_failed_verification_blocks_commit(
            root,
            failing_verifier,
        )

        verify_conflict_markers_rejected(
            root,
            passing_verifier,
        )

        verify_whitespace_errors_rejected(
            root,
            passing_verifier,
        )

    print("[PASS] Safe-commit dry-run preserves history")
    print("[PASS] Safe-commit creates reviewed commits")
    print("[PASS] Empty staged sets are rejected")
    print("[PASS] Failed verification blocks commits")
    print("[PASS] Failed verification preserves staged work")
    print("[PASS] Conflict markers are rejected")
    print("[PASS] Whitespace errors are rejected")
    print("[PASS] SafeCommitResult is immutable")
    print("----------------------------------------------------------------------")
    print("[PASS] All safe-commit contracts verified")


if __name__ == "__main__":
    main()

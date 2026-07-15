"""
JARVIS Gen 2 Phase VI-F5 verification-framework contracts.

All execution tests use temporary shell scripts and temporary output files.
The real phase suites are not executed by this test.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

from dev.verification.models import (
    SuiteDefinition,
    SuiteResult,
    VerificationReport,
)
from dev.verification.registry import (
    VERIFICATION_SUITES,
    validate_registry,
)
from dev.verification.runner import (
    build_report,
    execute_suite,
    select_suites,
    write_json_report,
)


def assert_frozen(
    instance: object,
    attribute_name: str,
    replacement: object,
) -> None:
    try:
        setattr(instance, attribute_name, replacement)
    except FrozenInstanceError:
        return

    raise AssertionError(
        f"{type(instance).__name__} must remain immutable"
    )


def create_script(
    path: Path,
    *,
    body: str,
) -> None:
    path.write_text(
        "#!/usr/bin/env bash\n"
        "set -Eeuo pipefail\n"
        + body
        + "\n",
        encoding="utf-8",
    )

    path.chmod(0o755)


def verify_registry_contracts() -> None:
    validate_registry()

    assert VERIFICATION_SUITES
    assert (
        VERIFICATION_SUITES[-1].suite_id
        == "7a1"
    )

    assert all(
        suite.required
        for suite in VERIFICATION_SUITES
    )

    assert len({
        suite.suite_id
        for suite in VERIFICATION_SUITES
    }) == len(VERIFICATION_SUITES)

    assert len({
        suite.script_path
        for suite in VERIFICATION_SUITES
    }) == len(VERIFICATION_SUITES)

    duplicate_ids = (
        SuiteDefinition(
            suite_id="duplicate",
            name="First",
            script_path="first.sh",
        ),
        SuiteDefinition(
            suite_id="duplicate",
            name="Second",
            script_path="second.sh",
        ),
    )

    try:
        validate_registry(duplicate_ids)
    except ValueError as exc:
        assert "IDs" in str(exc)
    else:
        raise AssertionError(
            "Duplicate registry IDs were accepted"
        )

    print("[PASS] Verification registry contracts")


def verify_suite_definition_contract() -> None:
    suite = SuiteDefinition(
        suite_id="test",
        name="Test Suite",
        script_path="dev/test.sh",
        required=True,
        category="tests",
        description="Contract fixture",
    )

    assert suite.suite_id == "test"
    assert suite.required is True
    assert suite.to_dict()["category"] == "tests"

    assert_frozen(
        suite,
        "suite_id",
        "changed",
    )

    for kwargs, message in (
        (
            {
                "suite_id": "",
                "name": "Name",
                "script_path": "script.sh",
            },
            "suite_id",
        ),
        (
            {
                "suite_id": "id",
                "name": "",
                "script_path": "script.sh",
            },
            "name",
        ),
        (
            {
                "suite_id": "id",
                "name": "Name",
                "script_path": "",
            },
            "script_path",
        ),
    ):
        try:
            SuiteDefinition(**kwargs)
        except ValueError as exc:
            assert message in str(exc)
        else:
            raise AssertionError(
                f"Invalid SuiteDefinition accepted: {kwargs}"
            )

    print("[PASS] SuiteDefinition immutable contract")


def verify_suite_selection() -> None:
    suites = (
        SuiteDefinition(
            suite_id="one",
            name="One",
            script_path="one.sh",
            category="alpha",
        ),
        SuiteDefinition(
            suite_id="two",
            name="Two",
            script_path="two.sh",
            category="beta",
        ),
        SuiteDefinition(
            suite_id="three",
            name="Three",
            script_path="three.sh",
            category="alpha",
        ),
    )

    selected = select_suites(
        suites,
        only_ids={"two"},
    )

    assert [
        suite.suite_id
        for suite in selected
    ] == [
        "two",
    ]

    selected = select_suites(
        suites,
        categories={"alpha"},
    )

    assert [
        suite.suite_id
        for suite in selected
    ] == [
        "one",
        "three",
    ]

    try:
        select_suites(
            suites,
            only_ids={"missing"},
        )
    except ValueError as exc:
        assert "Unknown" in str(exc)
    else:
        raise AssertionError(
            "Unknown suite ID was accepted"
        )

    print("[PASS] Suite filtering contracts")


def verify_execution_contracts(root: Path) -> tuple[
    SuiteResult,
    SuiteResult,
    SuiteResult,
    SuiteResult,
]:
    passing_script = root / "passing.sh"
    failing_script = root / "failing.sh"
    optional_missing = root / "optional-missing.sh"
    required_missing = root / "required-missing.sh"

    create_script(
        passing_script,
        body='echo "passing output"\nexit 0',
    )

    create_script(
        failing_script,
        body=(
            'echo "failing output"\n'
            'echo "failing error" >&2\n'
            "exit 7"
        ),
    )

    passing = execute_suite(
        SuiteDefinition(
            suite_id="passing",
            name="Passing",
            script_path=passing_script.name,
        ),
        root=root,
        python_bin="python",
    )

    failing = execute_suite(
        SuiteDefinition(
            suite_id="failing",
            name="Failing",
            script_path=failing_script.name,
        ),
        root=root,
        python_bin="python",
    )

    optional = execute_suite(
        SuiteDefinition(
            suite_id="optional",
            name="Optional Missing",
            script_path=optional_missing.name,
            required=False,
        ),
        root=root,
        python_bin="python",
    )

    required = execute_suite(
        SuiteDefinition(
            suite_id="required",
            name="Required Missing",
            script_path=required_missing.name,
            required=True,
        ),
        root=root,
        python_bin="python",
    )

    assert passing.status == "passed"
    assert passing.return_code == 0
    assert passing.passed
    assert not passing.blocks_success
    assert "passing output" in passing.stdout

    assert failing.status == "failed"
    assert failing.return_code == 7
    assert not failing.passed
    assert failing.blocks_success
    assert "failing output" in failing.stdout
    assert "failing error" in failing.stderr

    assert optional.status == "skipped"
    assert optional.return_code is None
    assert not optional.blocks_success

    assert required.status == "missing"
    assert required.return_code is None
    assert required.blocks_success

    print("[PASS] Suite execution and exit-code contracts")
    print("[PASS] Required and optional missing-suite behavior")
    print("[PASS] Standard output and error capture")

    return passing, failing, optional, required


def verify_report_contracts(
    root: Path,
    results: tuple[
        SuiteResult,
        SuiteResult,
        SuiteResult,
        SuiteResult,
    ],
) -> None:
    selected = tuple(
        SuiteDefinition(
            suite_id=result.suite_id,
            name=result.name,
            script_path=result.script_path,
            required=result.required,
            category=result.category,
        )
        for result in results
    )

    report = build_report(
        root=root,
        selected=selected,
        results=results,
        started_at="2026-07-13T12:00:00+00:00",
        completed_at="2026-07-13T12:00:01+00:00",
        elapsed_seconds=1.0,
    )

    assert isinstance(
        report,
        VerificationReport,
    )

    assert report.suites_executed == 2
    assert report.suites_passed == 1
    assert report.suites_failed == 2
    assert report.suites_skipped == 1
    assert report.suites_missing == 1
    assert report.passed is False

    assert_frozen(
        report,
        "elapsed_seconds",
        99.0,
    )

    output = root / "verification.json"

    write_json_report(
        report,
        output,
    )

    loaded = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert loaded["framework_version"] == "1.0"
    assert loaded["summary"]["passed"] is False
    assert loaded["summary"]["suites_executed"] == 2
    assert loaded["summary"]["suites_failed"] == 2
    assert len(loaded["results"]) == 4

    assert not output.with_suffix(
        output.suffix + ".tmp"
    ).exists()

    print("[PASS] VerificationReport summary semantics")
    print("[PASS] Atomic JSON report generation")
    print("[PASS] Machine-readable report schema")


def main() -> None:
    verify_registry_contracts()
    verify_suite_definition_contract()
    verify_suite_selection()

    with tempfile.TemporaryDirectory(
        prefix="jarvis-verification-framework-"
    ) as temporary:
        root = Path(temporary)

        results = verify_execution_contracts(root)
        verify_report_contracts(root, results)

    print("----------------------------------------------------------------------")
    print("[PASS] All verification-framework contracts verified")


if __name__ == "__main__":
    main()

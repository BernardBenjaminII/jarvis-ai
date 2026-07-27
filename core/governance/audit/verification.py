from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .filesystem import sha256_file
from .inventory import SCHEMA_VERSION
from .models import EvidenceClass, FileKind, RepositoryInventory, to_primitive

VERIFICATION_SCHEMA_VERSION = "1.1.0"
AUDIT_ENGINE_VERSION = "GENESIS-VII-C0-P1B-R1"
CANONICAL_ARTIFACTS = (
    "repository_inventory.json", "repository_statistics.json", "documentation_inventory.json",
    "verification_report.json", "manifest.json", "certification_report.md",
)


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    check_id: str
    description: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class RepositoryHealth:
    files_scanned: int
    source_files_verified: int
    generated_files_classified: int
    external_files_classified: int
    files_without_diagnostics: int
    files_with_diagnostics: int
    diagnostic_count: int
    coverage_percent: float
    status: str


@dataclass(frozen=True, slots=True)
class RepositoryVerificationReport:
    schema_version: str
    engine_version: str
    repository_fingerprint: str
    checks: tuple[VerificationCheck, ...]
    health: RepositoryHealth

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[VerificationCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


@dataclass(frozen=True, slots=True)
class RepositoryAuditManifest:
    manifest_schema_version: str
    audit_engine_version: str
    inventory_schema_version: str
    repository_name: str
    repository_fingerprint: str
    python_implementation: str
    python_version: str
    platform: str
    verification_passed: bool
    verification_report_fingerprint: str


class RepositoryInventoryVerifier:
    def verify(self, inventory: RepositoryInventory, *, root: Path | None = None) -> RepositoryVerificationReport:
        checks: list[VerificationCheck] = []
        checks.extend(self._verify_ordering(inventory))
        checks.extend(self._verify_uniqueness(inventory))
        checks.extend(self._verify_statistics(inventory))
        checks.extend(self._verify_cross_references(inventory))
        checks.extend(self._verify_fingerprint(inventory))
        checks.extend(self._verify_evidence_policy(inventory))
        if root is not None:
            checks.extend(self._verify_source_files(inventory, root))
        return RepositoryVerificationReport(
            schema_version=VERIFICATION_SCHEMA_VERSION, engine_version=AUDIT_ENGINE_VERSION,
            repository_fingerprint=inventory.fingerprint, checks=tuple(checks), health=self._build_health(inventory),
        )

    def build_manifest(self, inventory, report) -> RepositoryAuditManifest:
        return RepositoryAuditManifest(
            manifest_schema_version=VERIFICATION_SCHEMA_VERSION, audit_engine_version=AUDIT_ENGINE_VERSION,
            inventory_schema_version=inventory.schema_version, repository_name=inventory.root_name,
            repository_fingerprint=inventory.fingerprint, python_implementation=platform.python_implementation(),
            python_version=".".join(str(item) for item in sys.version_info[:3]), platform=platform.system(),
            verification_passed=report.passed, verification_report_fingerprint=_fingerprint(to_primitive(report)),
        )

    def write_outputs(self, report, manifest, output_directory: Path) -> None:
        output_directory.mkdir(parents=True, exist_ok=True)
        _write_json(output_directory / "verification_report.json", to_primitive(report))
        _write_json(output_directory / "manifest.json", to_primitive(manifest))
        (output_directory / "certification_report.md").write_text(render_certification_report(report, manifest), encoding="utf-8")

    def verify_artifacts(self, output_directory: Path, inventory: RepositoryInventory) -> tuple[VerificationCheck, ...]:
        missing = [name for name in CANONICAL_ARTIFACTS if not (output_directory / name).is_file()]
        invalid_json: list[str] = []
        for name in CANONICAL_ARTIFACTS:
            if not name.endswith(".json") or name in missing:
                continue
            try:
                json.loads((output_directory / name).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                invalid_json.append(name)
        fingerprint_ok = False
        try:
            inv = json.loads((output_directory / "repository_inventory.json").read_text(encoding="utf-8"))
            manifest = json.loads((output_directory / "manifest.json").read_text(encoding="utf-8"))
            fingerprint_ok = inv.get("fingerprint") == inventory.fingerprint == manifest.get("repository_fingerprint")
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
        return (
            _check("ARTIFACT-PRESENCE", "Canonical certification artifact set is complete", not missing, f"missing={len(missing)}" + (f"; first={missing[0]}" if missing else "")),
            _check("ARTIFACT-JSON", "Generated JSON artifacts are syntactically valid", not invalid_json, f"invalid={len(invalid_json)}" + (f"; first={invalid_json[0]}" if invalid_json else "")),
            _check("ARTIFACT-XREF", "Generated artifacts reference the current repository fingerprint", fingerprint_ok, f"fingerprint={inventory.fingerprint}"),
        )

    @staticmethod
    def _verify_ordering(inventory) -> Iterable[VerificationCheck]:
        groups = (("ORDER-FILES", "Repository files", [x.path for x in inventory.files]),
                  ("ORDER-PYTHON", "Python modules", [x.path for x in inventory.python_modules]),
                  ("ORDER-MARKDOWN", "Markdown documents", [x.path for x in inventory.markdown_documents]))
        for cid, label, values in groups:
            yield _check(cid, f"{label} use deterministic path ordering", values == sorted(values), f"count={len(values)}")
        keys = [(x.path, x.parser, x.line or 0, x.message) for x in inventory.diagnostics]
        yield _check("ORDER-DIAGNOSTICS", "Diagnostics use deterministic ordering", keys == sorted(keys), f"count={len(keys)}")

    @staticmethod
    def _verify_uniqueness(inventory) -> Iterable[VerificationCheck]:
        for cid, label, values in (
            ("UNIQUE-PATHS", "Repository paths", [x.path for x in inventory.files]),
            ("UNIQUE-IDS", "Repository identifiers", [x.repository_id for x in inventory.files]),
            ("UNIQUE-PYTHON", "Python module paths", [x.path for x in inventory.python_modules]),
            ("UNIQUE-MARKDOWN", "Markdown document paths", [x.path for x in inventory.markdown_documents]),
        ):
            yield _check(cid, f"{label} are unique", len(values) == len(set(values)), f"count={len(values)}")

    @staticmethod
    def _verify_statistics(inventory) -> Iterable[VerificationCheck]:
        expected = {
            "total_files": len(inventory.files), "total_bytes": sum(x.size_bytes for x in inventory.files),
            "python_files": sum(x.kind is FileKind.PYTHON for x in inventory.files),
            "markdown_files": sum(x.kind is FileKind.MARKDOWN for x in inventory.files),
            "shell_files": sum(x.kind is FileKind.SHELL for x in inventory.files),
            "package_markers": sum(x.is_package_marker for x in inventory.files),
            "test_files": sum(x.is_test for x in inventory.files),
            "verification_files": sum(x.is_verification for x in inventory.files),
            "architecture_documents": sum(x.is_architecture_document for x in inventory.files),
            "adr_documents": sum(x.is_adr for x in inventory.files),
            "constitutional_documents": sum(x.is_constitutional_document for x in inventory.files),
            "whitepapers": sum(x.is_whitepaper for x in inventory.files),
            "python_modules": len(inventory.python_modules),
            "python_symbols": sum(len(x.symbols) for x in inventory.python_modules),
            "markdown_documents": len(inventory.markdown_documents), "diagnostics": len(inventory.diagnostics),
            "source_files": sum(x.evidence_class is EvidenceClass.SOURCE for x in inventory.files),
            "generated_files": sum(x.evidence_class is EvidenceClass.GENERATED for x in inventory.files),
            "external_files": sum(x.evidence_class is EvidenceClass.EXTERNAL for x in inventory.files),
        }
        for name, value in expected.items():
            actual = getattr(inventory.statistics, name)
            yield _check(f"STAT-{name.upper()}", f"Statistic {name} matches inventory evidence", actual == value, f"expected={value}; actual={actual}")

    @staticmethod
    def _verify_cross_references(inventory) -> Iterable[VerificationCheck]:
        files = {x.path: x for x in inventory.files}
        py = {x.path for x in inventory.python_modules}; md = {x.path for x in inventory.markdown_documents}
        yield _check("XREF-PYTHON", "Every Python file has exactly one parsed module", py == {x.path for x in inventory.files if x.kind is FileKind.PYTHON}, f"actual={len(py)}")
        yield _check("XREF-MARKDOWN", "Every Markdown file has exactly one parsed document", md == {x.path for x in inventory.files if x.kind is FileKind.MARKDOWN}, f"actual={len(md)}")
        yield _check("XREF-IDS", "Parsed objects retain source repository identifiers", all(files[x.path].repository_id == x.repository_id for x in (*inventory.python_modules, *inventory.markdown_documents)), "compared by path")
        yield _check("XREF-DIAGNOSTICS", "Every diagnostic references a discovered file", all(x.path in files for x in inventory.diagnostics), f"diagnostics={len(inventory.diagnostics)}")

    @staticmethod
    def _verify_fingerprint(inventory) -> Iterable[VerificationCheck]:
        provisional = {"schema_version": inventory.schema_version, "root_name": inventory.root_name,
            "files": to_primitive(inventory.files), "python_modules": to_primitive(inventory.python_modules),
            "markdown_documents": to_primitive(inventory.markdown_documents),
            "diagnostics": to_primitive(inventory.diagnostics), "statistics": to_primitive(inventory.statistics)}
        actual = _fingerprint(provisional)
        yield _check("FINGERPRINT", "Repository fingerprint matches canonical inventory evidence", actual == inventory.fingerprint, f"expected={inventory.fingerprint}; actual={actual}")
        yield _check("SCHEMA", "Inventory schema is supported", inventory.schema_version == SCHEMA_VERSION, f"expected={SCHEMA_VERSION}; actual={inventory.schema_version}")

    @staticmethod
    def _verify_evidence_policy(inventory) -> Iterable[VerificationCheck]:
        valid = all(isinstance(x.evidence_class, EvidenceClass) for x in inventory.files)
        generated_under_artifacts = all(x.evidence_class is EvidenceClass.GENERATED for x in inventory.files if x.path.split("/", 1)[0].casefold() in {"artifacts", "reports", "logs", "coverage", "htmlcov", "dist", "build"})
        yield _check("EVIDENCE-CLASS", "Every repository file has a recognized evidence classification", valid, f"files={len(inventory.files)}")
        yield _check("EVIDENCE-GENERATED", "Generated-root files are never classified as immutable source evidence", generated_under_artifacts, "generated roots checked")

    @staticmethod
    def _verify_source_files(inventory, root: Path) -> Iterable[VerificationCheck]:
        root = root.expanduser().resolve(); missing = []; changed = []; verified = 0
        for item in inventory.files:
            if item.evidence_class is not EvidenceClass.SOURCE:
                continue
            verified += 1; path = root / item.path
            if not path.is_file(): missing.append(item.path); continue
            if path.stat().st_size != item.size_bytes or sha256_file(path) != item.sha256: changed.append(item.path)
        yield _check("SOURCE-PRESENCE", "Every inventoried source file remains present", not missing, f"verified={verified}; missing={len(missing)}" + (f"; first={missing[0]}" if missing else ""))
        yield _check("SOURCE-HASHES", "Every inventoried source file retains its recorded content hash", not changed, f"verified={verified}; changed={len(changed)}" + (f"; first={changed[0]}" if changed else ""))

    @staticmethod
    def _build_health(inventory) -> RepositoryHealth:
        with_diag = len({x.path for x in inventory.diagnostics}); total = inventory.statistics.total_files
        without = max(total - with_diag, 0); coverage = 100.0 if total == 0 else round(without / total * 100.0, 6)
        status = "EXCELLENT" if coverage == 100.0 else "GOOD" if coverage >= 99.0 else "DEGRADED" if coverage >= 95.0 else "FAILED"
        return RepositoryHealth(total, inventory.statistics.source_files, inventory.statistics.generated_files,
            inventory.statistics.external_files, without, with_diag, len(inventory.diagnostics), coverage, status)


def render_certification_report(report, manifest) -> str:
    lines = ["# Genesis VII-C0 Pack 1B-R1 — Repository Discovery Certification", "",
        f"**Engine version:** `{report.engine_version}`  ", f"**Repository:** `{manifest.repository_name}`  ",
        f"**Repository fingerprint:** `{report.repository_fingerprint}`  ",
        f"**Overall result:** `{'PASS' if report.passed else 'FAIL'}`  ", f"**Repository health:** `{report.health.status}`  ", "",
        "## Verification Checks", "", "| Check | Result | Description | Detail |", "|---|---|---|---|"]
    for c in report.checks:
        lines.append(f"| `{c.check_id}` | **{'PASS' if c.passed else 'FAIL'}** | {c.description} | {c.detail.replace('|', '\\|')} |")
    lines += ["", "## Evidence Classification", "", f"- Source files: **{report.health.source_files_verified}**",
        f"- Generated files: **{report.health.generated_files_classified}**", f"- External files: **{report.health.external_files_classified}**", "",
        "## Certification Decision", "", "Repository Discovery Engine evidence is certified for constitutional audit use." if report.passed else "Repository Discovery Engine evidence is not certified. Resolve failed checks and rerun verification.", ""]
    return "\n".join(lines)


def _check(check_id, description, passed, detail): return VerificationCheck(check_id, description, passed, detail)
def _canonical_json(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
def _fingerprint(value): return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
def _write_json(path, value): path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

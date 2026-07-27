from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from core.governance.audit import RepositoryInventory

from .contracts import (
    CONSTITUTIONAL_EXTRACTION_SCHEMA_VERSION,
    ENGINE_VERSION,
    ClaimModality,
    DiagnosticSeverity,
    ExtractionStatus,
)
from .markdown import extract_units
from .models import (
    ConstitutionalClaim,
    ConstitutionalExtractionReport,
    ConstitutionalExtractionStatistics,
    ConstitutionalSource,
    EvidenceLocator,
    ExtractionDiagnostic,
    ExtractionPolicy,
    to_primitive,
)
from .rules import detect_modality, infer_domain

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9`*])")
_RATIFIED_STATUS = re.compile(r"\b(?:ratified|certified|approved|canonical|active)\b", re.I)


class ConstitutionalExtractionEngine:
    """Deterministically extracts reviewable constitutional claims from certified repository evidence."""

    def __init__(self, policy: ExtractionPolicy | None = None) -> None:
        self.policy = policy or ExtractionPolicy()

    def extract(
        self,
        *,
        root: Path,
        inventory: RepositoryInventory,
        output_directory: Path | None = None,
    ) -> ConstitutionalExtractionReport:
        root = root.expanduser().resolve()
        file_by_path = {item.path: item for item in inventory.files}
        sources: list[ConstitutionalSource] = []
        claims: list[ConstitutionalClaim] = []
        diagnostics: list[ExtractionDiagnostic] = []

        for document in inventory.markdown_documents:
            repository_file = file_by_path.get(document.path)
            if repository_file is None or not self._eligible(repository_file):
                continue
            path = root / document.path
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="replace")
                diagnostics.append(ExtractionDiagnostic(document.path, "Invalid UTF-8 replaced during extraction", DiagnosticSeverity.WARNING))
            except OSError as exc:
                diagnostics.append(ExtractionDiagnostic(document.path, f"Unable to read source: {exc}", DiagnosticSeverity.ERROR))
                continue

            source_kind = self._source_kind(repository_file)
            source = ConstitutionalSource(
                repository_id=repository_file.repository_id,
                path=document.path,
                document_id=document.document_id,
                title=document.title,
                source_sha256=repository_file.sha256,
                source_kind=source_kind,
                status=document.status,
            )
            source_claims = self._extract_document(source, text)
            if source_claims or source_kind == "constitutional":
                sources.append(source)
                claims.extend(source_claims)

        sources.sort(key=lambda item: item.path)
        claims.sort(key=lambda item: (item.locator.path, item.locator.start_line, item.claim_id))
        diagnostics.sort(key=lambda item: (item.path, item.line or 0, item.message))
        statistics = self._statistics(claims, diagnostics, sources)
        provisional = {
            "schema_version": CONSTITUTIONAL_EXTRACTION_SCHEMA_VERSION,
            "engine_version": ENGINE_VERSION,
            "repository_fingerprint": inventory.fingerprint,
            "sources": to_primitive(tuple(sources)),
            "claims": to_primitive(tuple(claims)),
            "diagnostics": to_primitive(tuple(diagnostics)),
            "statistics": to_primitive(statistics),
        }
        fingerprint = _fingerprint(provisional)
        report = ConstitutionalExtractionReport(
            schema_version=CONSTITUTIONAL_EXTRACTION_SCHEMA_VERSION,
            engine_version=ENGINE_VERSION,
            repository_fingerprint=inventory.fingerprint,
            sources=tuple(sources),
            claims=tuple(claims),
            diagnostics=tuple(diagnostics),
            statistics=statistics,
            fingerprint=fingerprint,
        )
        if output_directory is not None:
            self.write_outputs(report, output_directory)
        return report

    def write_outputs(self, report: ConstitutionalExtractionReport, output_directory: Path) -> None:
        output_directory.mkdir(parents=True, exist_ok=True)
        _write_json(output_directory / "constitutional_extraction.json", to_primitive(report))
        _write_json(output_directory / "constitutional_claims.json", {
            "schema_version": report.schema_version,
            "repository_fingerprint": report.repository_fingerprint,
            "extraction_fingerprint": report.fingerprint,
            "claims": to_primitive(report.claims),
        })
        _write_json(output_directory / "constitutional_sources.json", {
            "schema_version": report.schema_version,
            "repository_fingerprint": report.repository_fingerprint,
            "extraction_fingerprint": report.fingerprint,
            "sources": to_primitive(report.sources),
        })
        (output_directory / "constitutional_extraction_report.md").write_text(_render_markdown(report), encoding="utf-8")

    def _eligible(self, file) -> bool:
        return bool(
            (self.policy.include_constitutional_documents and file.is_constitutional_document)
            or (self.policy.include_architecture_documents and file.is_architecture_document)
            or (self.policy.include_adrs and file.is_adr)
        )

    @staticmethod
    def _source_kind(file) -> str:
        if file.is_constitutional_document:
            return "constitutional"
        if file.is_adr:
            return "adr"
        if file.is_architecture_document:
            return "architecture"
        return "documentation"

    def _extract_document(self, source: ConstitutionalSource, text: str) -> tuple[ConstitutionalClaim, ...]:
        claims: list[ConstitutionalClaim] = []
        seen: set[tuple[int, str]] = set()
        ratified = bool(source.status and _RATIFIED_STATUS.search(source.status))
        for unit in extract_units(text):
            for sentence in _split_sentences(unit.text):
                cleaned = _normalize_display(sentence)
                if not (self.policy.minimum_text_length <= len(cleaned) <= self.policy.maximum_claim_length):
                    continue
                modality = detect_modality(cleaned)
                if modality is None:
                    if not self.policy.include_non_normative_declarations:
                        continue
                    modality = ClaimModality.DECLARATION
                normalized = _normalize_claim(cleaned)
                key = (unit.start_line, normalized)
                if key in seen:
                    continue
                seen.add(key)
                domain, domain_basis = infer_domain(cleaned, unit.section_path, source.path)
                status = ExtractionStatus.RATIFIED_SOURCE if ratified else ExtractionStatus.CANDIDATE
                if modality is ClaimModality.DECLARATION:
                    status = ExtractionStatus.REVIEW_REQUIRED
                locator = EvidenceLocator(
                    path=source.path,
                    start_line=unit.start_line,
                    end_line=unit.end_line,
                    section_path=unit.section_path,
                    excerpt_sha256=hashlib.sha256(cleaned.encode("utf-8")).hexdigest(),
                )
                claim_id = _claim_id(source.repository_id, unit.start_line, normalized)
                basis = (f"modality:{modality.value}", *domain_basis, f"source:{source.source_kind}")
                claims.append(ConstitutionalClaim(
                    claim_id=claim_id,
                    source_repository_id=source.repository_id,
                    source_document_id=source.document_id,
                    text=cleaned,
                    normalized_text=normalized,
                    modality=modality,
                    domain=domain,
                    status=status,
                    locator=locator,
                    confidence_basis=tuple(basis),
                ))
        return tuple(claims)

    @staticmethod
    def _statistics(claims, diagnostics, sources) -> ConstitutionalExtractionStatistics:
        domains = Counter(item.domain.value for item in claims)
        modalities = Counter(item.modality.value for item in claims)
        normative = sum(item.modality is not ClaimModality.DECLARATION for item in claims)
        return ConstitutionalExtractionStatistics(
            source_documents=len(sources), claims=len(claims), normative_claims=normative,
            declarations=len(claims) - normative,
            review_required=sum(item.status is ExtractionStatus.REVIEW_REQUIRED for item in claims),
            diagnostics=len(diagnostics), domains=tuple(sorted(domains.items())),
            modalities=tuple(sorted(modalities.items())),
        )


def _split_sentences(text: str) -> tuple[str, ...]:
    parts = tuple(item.strip() for item in _SENTENCE_BOUNDARY.split(text) if item.strip())
    return parts or (text.strip(),)


def _normalize_display(text: str) -> str:
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_claim(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _claim_id(repository_id: str, line: int, normalized: str) -> str:
    digest = hashlib.sha256(f"{repository_id}|{line}|{normalized}".encode("utf-8")).hexdigest()[:16].upper()
    return f"CCL-{digest}"


def _canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _fingerprint(value) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_markdown(report: ConstitutionalExtractionReport) -> str:
    lines = [
        "# Constitutional Extraction Report", "",
        f"**Schema:** `{report.schema_version}`  ",
        f"**Engine:** `{report.engine_version}`  ",
        f"**Repository fingerprint:** `{report.repository_fingerprint}`  ",
        f"**Extraction fingerprint:** `{report.fingerprint}`", "",
        "## Summary", "",
        f"- Source documents: {report.statistics.source_documents}",
        f"- Claims: {report.statistics.claims}",
        f"- Normative claims: {report.statistics.normative_claims}",
        f"- Review required: {report.statistics.review_required}",
        f"- Diagnostics: {report.statistics.diagnostics}", "",
        "## Claims", "",
    ]
    for claim in report.claims:
        section = " / ".join(claim.locator.section_path) or "Document root"
        lines.extend((
            f"### {claim.claim_id}", "",
            f"- **Domain:** `{claim.domain.value}`",
            f"- **Modality:** `{claim.modality.value}`",
            f"- **Status:** `{claim.status.value}`",
            f"- **Evidence:** `{claim.locator.path}:{claim.locator.start_line}-{claim.locator.end_line}`",
            f"- **Section:** {section}", "",
            claim.text, "",
        ))
    return "\n".join(lines).rstrip() + "\n"

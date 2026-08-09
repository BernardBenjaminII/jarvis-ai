from __future__ import annotations

import json
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .adapter import MaterializerAdapter
from .candidates import discover_candidates
from .checkpoint import CheckpointStore
from .contracts import (
    BatchReport,
    CampaignConfig,
    CampaignRunReport,
    Candidate,
    CandidateDisposition,
    CandidateResult,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FullCorpusMaterializationCampaign:
    def __init__(self, config: CampaignConfig) -> None:
        self.config = config
        self.store = CheckpointStore(config.checkpoint_db)

    def prepare(
        self,
        *,
        inventory_catalog: Path,
    ) -> dict[str, int]:
        candidates = discover_candidates(
            runtime_catalog=self.config.runtime_catalog,
            inventory_catalog=inventory_catalog,
            knowledge_root=self.config.knowledge_root,
        )
        inserted = self.store.register_candidates(candidates)
        self.store.set_state("prepared_at", _now())
        self.store.set_state(
            "inventory_catalog",
            str(inventory_catalog.resolve()),
        )
        self.store.set_state(
            "runtime_catalog",
            str(self.config.runtime_catalog.resolve()),
        )
        return {
            "discovered": len(candidates),
            "inserted": inserted,
            "registered_total": self.store.candidate_count(),
        }

    def _process_candidate(
        self,
        *,
        adapter: MaterializerAdapter,
        candidate: Candidate,
    ) -> CandidateResult:
        started = time.monotonic()
        self.store.mark_attempt(candidate.candidate_id)

        path = Path(candidate.path)

        if not path.is_file():
            return CandidateResult(
                candidate_id=candidate.candidate_id,
                path=candidate.path,
                disposition=CandidateDisposition.SKIPPED_MISSING,
                detail="Source file is not present.",
                elapsed_seconds=time.monotonic() - started,
            )

        try:
            if path.stat().st_size <= 0:
                return CandidateResult(
                    candidate_id=candidate.candidate_id,
                    path=candidate.path,
                    disposition=CandidateDisposition.SKIPPED_EMPTY,
                    detail="Source file is empty.",
                    elapsed_seconds=time.monotonic() - started,
                )
        except OSError as exc:
            return CandidateResult(
                candidate_id=candidate.candidate_id,
                path=candidate.path,
                disposition=CandidateDisposition.QUARANTINED,
                detail=f"{type(exc).__name__}: {exc}",
                elapsed_seconds=time.monotonic() - started,
            )

        if self.config.dry_run:
            return CandidateResult(
                candidate_id=candidate.candidate_id,
                path=candidate.path,
                disposition=CandidateDisposition.PENDING,
                detail="Dry run: candidate validated but not materialized.",
                elapsed_seconds=time.monotonic() - started,
            )

        pre = adapter.table_counts()

        try:
            adapter.materialize(candidate)
        except Exception as exc:
            return CandidateResult(
                candidate_id=candidate.candidate_id,
                path=candidate.path,
                disposition=CandidateDisposition.FAILED_MATERIALIZATION,
                detail=f"{type(exc).__name__}: {exc}",
                elapsed_seconds=time.monotonic() - started,
            )

        post = adapter.table_counts()
        document_delta = (
            post["runtime_documents"]
            - pre["runtime_documents"]
        )
        chunk_delta = (
            post["runtime_chunks"]
            - pre["runtime_chunks"]
        )
        fts_delta = (
            post["runtime_chunks_fts"]
            - pre["runtime_chunks_fts"]
        )

        if document_delta <= 0:
            disposition = CandidateDisposition.SKIPPED_ALREADY_PRESENT
            detail = (
                "Materializer completed without creating a new runtime document."
            )
        elif chunk_delta <= 0:
            disposition = CandidateDisposition.FAILED_EXTRACTION
            detail = (
                "Runtime document was created but no runtime chunks were added."
            )
        elif fts_delta != chunk_delta:
            disposition = CandidateDisposition.QUARANTINED
            detail = (
                "Runtime chunk and FTS deltas differ: "
                f"chunks={chunk_delta}, fts={fts_delta}."
            )
        else:
            disposition = CandidateDisposition.MATERIALIZED
            detail = (
                f"Materialized with {chunk_delta} chunks and "
                f"{fts_delta} FTS rows."
            )

        return CandidateResult(
            candidate_id=candidate.candidate_id,
            path=candidate.path,
            disposition=disposition,
            detail=detail,
            runtime_document_delta=document_delta,
            runtime_chunk_delta=chunk_delta,
            runtime_fts_delta=fts_delta,
            elapsed_seconds=time.monotonic() - started,
        )

    def run(self) -> CampaignRunReport:
        campaign_id = (
            self.store.get_state("campaign_id")
            or f"IX-A6-{uuid.uuid4().hex[:12]}"
        )
        self.store.set_state("campaign_id", campaign_id)

        started_at = _now()
        started = time.monotonic()
        adapter = MaterializerAdapter(
            runtime_catalog=self.config.runtime_catalog,
        )
        pre_counts = adapter.table_counts()
        batch_reports = []
        examined = 0
        batch_ordinal = 0

        while True:
            if (
                self.config.max_batches is not None
                and batch_ordinal >= self.config.max_batches
            ):
                break

            remaining_limit = self.config.batch_size

            if self.config.max_documents is not None:
                remaining = (
                    self.config.max_documents - examined
                )
                if remaining <= 0:
                    break
                remaining_limit = min(
                    remaining_limit,
                    remaining,
                )

            candidates = self.store.next_candidates(
                limit=remaining_limit,
                retry_failures=self.config.retry_failures,
            )

            if not candidates:
                break

            batch_ordinal += 1
            batch_id = (
                f"{campaign_id}-B{batch_ordinal:06d}"
            )
            batch_started_at = _now()
            batch_started = time.monotonic()
            batch_pre = adapter.table_counts()

            self.store.start_batch(
                batch_id=batch_id,
                ordinal=batch_ordinal,
                candidate_count=len(candidates),
                started_at=batch_started_at,
            )

            results = []

            for candidate in candidates:
                result = self._process_candidate(
                    adapter=adapter,
                    candidate=candidate,
                )
                results.append(result)

                if not self.config.dry_run:
                    self.store.record_result(result)

                examined += 1

                if (
                    self.config.stop_on_error
                    and result.disposition
                    in {
                        CandidateDisposition.FAILED_EXTRACTION,
                        CandidateDisposition.FAILED_MATERIALIZATION,
                        CandidateDisposition.QUARANTINED,
                    }
                ):
                    break

            batch_post = adapter.table_counts()
            batch_completed_at = _now()
            batch_elapsed = time.monotonic() - batch_started
            batch_status = (
                "DRY_RUN"
                if self.config.dry_run
                else (
                    "FAILED"
                    if any(
                        item.disposition
                        in {
                            CandidateDisposition.FAILED_EXTRACTION,
                            CandidateDisposition.FAILED_MATERIALIZATION,
                            CandidateDisposition.QUARANTINED,
                        }
                        for item in results
                    )
                    else "COMPLETED"
                )
            )

            batch_report = BatchReport(
                batch_id=batch_id,
                ordinal=batch_ordinal,
                candidate_count=len(candidates),
                started_at=batch_started_at,
                completed_at=batch_completed_at,
                elapsed_seconds=batch_elapsed,
                status=batch_status,
                results=tuple(results),
                pre_counts=batch_pre,
                post_counts=batch_post,
            )
            batch_reports.append(batch_report)

            self.store.complete_batch(
                batch_id=batch_id,
                completed_at=batch_completed_at,
                status=batch_status,
                report_json=json.dumps(
                    batch_report.to_dict(),
                    sort_keys=True,
                ),
            )

            if self.config.dry_run:
                break

            if (
                self.config.stop_on_error
                and batch_status == "FAILED"
            ):
                break

        post_counts = adapter.table_counts()
        completed_at = _now()
        elapsed = time.monotonic() - started

        if self.config.dry_run:
            disposition_counts = Counter(
                result.disposition.value
                for report in batch_reports
                for result in report.results
            )
        else:
            disposition_counts = Counter(
                self.store.disposition_counts()
            )

        fts_consistent = (
            post_counts["runtime_chunks"]
            == post_counts["runtime_chunks_fts"]
        )
        failed_count = sum(
            int(disposition_counts.get(name, 0))
            for name in (
                CandidateDisposition.FAILED_EXTRACTION.value,
                CandidateDisposition.FAILED_MATERIALIZATION.value,
                CandidateDisposition.QUARANTINED.value,
            )
        )

        if self.config.dry_run:
            classification = "CAMPAIGN_DRY_RUN_READY"
            status = "EXCELLENT"
        elif not fts_consistent:
            classification = "CAMPAIGN_FTS_INTEGRITY_FAILURE"
            status = "FAILED"
        elif failed_count:
            classification = "CAMPAIGN_COMPLETED_WITH_FAILURES"
            status = "FAILED"
        else:
            classification = "CAMPAIGN_BATCHES_COMPLETED"
            status = "EXCELLENT"

        recommendations = []

        if self.config.dry_run:
            recommendations.append(
                "Review the dry-run candidate count, then launch a bounded execution batch."
            )
        else:
            recommendations.append(
                "Continue with the next bounded batch until no PENDING candidates remain."
            )
            recommendations.append(
                "Review quarantined and failed candidates before enabling retries."
            )

        if fts_consistent:
            recommendations.append(
                "Runtime chunk and FTS counts remain synchronized."
            )
        else:
            recommendations.append(
                "Stop the campaign and repair FTS synchronization before resuming."
            )

        return CampaignRunReport(
            campaign_id=campaign_id,
            status=status,
            classification=classification,
            started_at=started_at,
            completed_at=completed_at,
            elapsed_seconds=elapsed,
            dry_run=self.config.dry_run,
            batches_completed=len(batch_reports),
            candidates_examined=examined,
            disposition_counts=dict(
                sorted(disposition_counts.items())
            ),
            pre_counts=pre_counts,
            post_counts=post_counts,
            checkpoint_db=str(
                self.config.checkpoint_db.resolve()
            ),
            reports=tuple(batch_reports),
            recommendations=tuple(recommendations),
        )

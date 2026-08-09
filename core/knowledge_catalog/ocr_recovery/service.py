from __future__ import annotations
import hashlib
import mimetypes
import shutil
import tempfile
import time
from pathlib import Path

from core.knowledge_catalog.advanced_extraction.checkpoint import failed_candidates
from core.knowledge_catalog.materialization import chunk_text, extract_text
from core.knowledge_catalog.production_materialization.models import Artifact
from core.knowledge_catalog.production_materialization.checkpoint import CheckpointStore
from core.knowledge_catalog.production_materialization.reliability import ReliableSQLite, SQLiteReliabilityPolicy
from core.knowledge_catalog.production_materialization.writer_batch import BatchedRuntimeWriter

from .dependencies import tesseract_info
from .models import OCRPolicy, OCRCandidateResult
from .ocr import ocr_pdf
from .pdf_repair import inspect_pdf, reconstruct_pdf
from .quality import quality_score
from .store import OCRRecoveryStore

def digest(text:str)->str:
    return hashlib.sha256(text.encode("utf-8",errors="ignore")).hexdigest()

class OCRRecoveryService:
    def __init__(self,*,runtime_catalog:Path,checkpoint_db:Path,recovery_db:Path,
                 work_dir:Path,policy:OCRPolicy):
        self.runtime_catalog=runtime_catalog
        self.checkpoint_db=checkpoint_db
        self.work_dir=work_dir
        self.policy=policy
        self.store=OCRRecoveryStore(recovery_db)
        self.checkpoint=CheckpointStore(checkpoint_db)
        self.sqlite=ReliableSQLite(runtime_catalog,SQLiteReliabilityPolicy())
        self.sqlite.configure_runtime_database()
        self.writer=BatchedRuntimeWriter(
            reliable_sqlite=self.sqlite,
            checkpoint_store=self.checkpoint,
        )

    def candidates(self):
        return failed_candidates(self.checkpoint_db)

    def classify(self,candidate):
        p=Path(candidate.path)
        if not p.is_file():
            return OCRCandidateResult(candidate.candidate_id,candidate.path,
                "MISSING_SOURCE","inspection","Source file missing.")

        if candidate.extension.casefold() != ".pdf":
            return OCRCandidateResult(candidate.candidate_id,candidate.path,
                "NON_PDF_REVIEW","inspection",
                f"OCR recovery only handles PDF; extension={candidate.extension}")

        info=inspect_pdf(p)
        if not info["openable"]:
            return OCRCandidateResult(candidate.candidate_id,candidate.path,
                "REPAIR_REQUIRED","pdf_structure",
                info["error"] or "PDF could not be opened.")
        if info["needs_password"]:
            return OCRCandidateResult(candidate.candidate_id,candidate.path,
                "ENCRYPTED","pdf_structure","Encrypted PDF requires password.",
                pages_total=info["pages"])

        return OCRCandidateResult(candidate.candidate_id,candidate.path,
            "OCR_CANDIDATE","pdf_structure",
            f"PDF is openable with {info['pages']} pages.",
            pages_total=info["pages"])

    def recover_one(self,candidate,dry_run=False):
        initial=self.classify(candidate)
        if initial.status in {"MISSING_SOURCE","NON_PDF_REVIEW","ENCRYPTED"}:
            self.store.record(candidate,initial)
            return initial

        p=Path(candidate.path)
        working=p
        repaired=False

        if initial.status=="REPAIR_REQUIRED":
            target=self.work_dir/"repaired"/f"{candidate.candidate_id.replace(':','_')}.pdf"
            ok,detail=reconstruct_pdf(p,target)
            if not ok:
                result=OCRCandidateResult(candidate.candidate_id,candidate.path,
                    "UNRECOVERABLE","pdf_repair",detail)
                self.store.record(candidate,result)
                return result
            working=target
            repaired=True

        # native salvage after repair/open
        try:
            native=str(extract_text(working) or "")
        except Exception:
            native=""

        if len(native.strip()) >= self.policy.minimum_chars and quality_score(native) >= self.policy.minimum_quality:
            result=OCRCandidateResult(candidate.candidate_id,candidate.path,
                "RECOVERABLE_NATIVE",
                "repaired_native" if repaired else "native_retry",
                "Recovered acceptable native text.",
                text=native,chars=len(native),
                quality_score=quality_score(native))
            self.store.record(candidate,result)
            return result

        dep=tesseract_info()
        if not dep["available"]:
            result=OCRCandidateResult(candidate.candidate_id,candidate.path,
                "OCR_UNAVAILABLE","ocr_dependency",
                "Tesseract is not installed or not on PATH.")
            self.store.record(candidate,result)
            return result

        missing=[lang for lang in self.policy.languages.split("+") if lang and lang not in dep["languages"]]
        if missing:
            result=OCRCandidateResult(candidate.candidate_id,candidate.path,
                "OCR_LANGUAGE_MISSING","ocr_dependency",
                f"Missing Tesseract language data: {', '.join(missing)}")
            self.store.record(candidate,result)
            return result

        if dry_run:
            result=OCRCandidateResult(candidate.candidate_id,candidate.path,
                "OCR_READY","ocr_dry_run",
                f"Tesseract available; would OCR up to {self.policy.max_pages} pages.",
                pages_total=initial.pages_total)
            self.store.record(candidate,result)
            return result

        try:
            text,meta=ocr_pdf(working,self.policy,tesseract_path=dep["path"])
        except Exception as exc:
            result=OCRCandidateResult(candidate.candidate_id,candidate.path,
                "OCR_FAILED","ocr",
                f"{type(exc).__name__}: {exc}")
            self.store.record(candidate,result)
            return result

        score=meta["quality_score"]
        if len(text.strip()) < self.policy.minimum_chars or score < self.policy.minimum_quality:
            result=OCRCandidateResult(candidate.candidate_id,candidate.path,
                "OCR_LOW_QUALITY","ocr",
                "OCR output did not pass quality gate.",
                text="",chars=len(text),pages_total=meta["pages_total"],
                pages_attempted=meta["pages_attempted"],
                pages_recovered=meta["pages_recovered"],quality_score=score)
            self.store.record(candidate,result)
            return result

        result=OCRCandidateResult(candidate.candidate_id,candidate.path,
            "RECOVERABLE_OCR",
            "repaired_ocr" if repaired else "ocr",
            "OCR passed quality gate.",
            text=text,chars=len(text),pages_total=meta["pages_total"],
            pages_attempted=meta["pages_attempted"],
            pages_recovered=meta["pages_recovered"],quality_score=score)
        self.store.record(candidate,result)
        return result

    def artifact(self,candidate,result):
        text=result.text
        chunks=[]
        for idx,(start,end,value) in enumerate(chunk_text(
            text,target_chars=3200,overlap_chars=320,minimum_chars=120
        )):
            chunks.append({
                "chunk_index":idx,"chunk_text":value,"start_char":int(start),
                "end_char":int(end),"token_estimate":max(1,len(value)//4),
                "content_sha256":digest(value),
            })
        if not chunks:
            raise ValueError("Recovered text produced no chunks.")
        return Artifact(
            candidate.candidate_id,candidate.path,candidate.title,candidate.category,
            candidate.sha256 or digest(text),
            mimetypes.guess_type(candidate.path)[0] or "application/pdf",
            text,tuple(chunks),0.0,
        )

    def recover(self,candidates,*,dry_run=False,writer_batch_size=5):
        outcomes=[]
        pending=[]
        for candidate in candidates:
            started=time.monotonic()
            result=self.recover_one(candidate,dry_run=dry_run)
            outcomes.append(result)
            if result.status in {"RECOVERABLE_NATIVE","RECOVERABLE_OCR"} and not dry_run:
                artifact=self.artifact(candidate,result)
                artifact=Artifact(
                    artifact.candidate_id,artifact.path,artifact.title,artifact.category,
                    artifact.sha256,artifact.media_type,artifact.content_text,artifact.chunks,
                    time.monotonic()-started,
                )
                pending.append(artifact)
                if len(pending)>=writer_batch_size:
                    self.writer.write_batch(pending); pending=[]
        if pending:
            self.writer.write_batch(pending)
        return outcomes

    def runtime_counts(self):
        c=self.sqlite.connect(read_only=True)
        try:
            return {
                t:int(c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0])
                for t in ("runtime_documents","runtime_chunks","runtime_chunks_fts")
            }
        finally:
            c.close()

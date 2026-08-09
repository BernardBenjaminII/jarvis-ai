from __future__ import annotations
from pathlib import Path
from .classifier import classify_filesystem_artifact
from .checkpoint import failed_items,set_stage,stage_counts
from .runtime_cleanup import has_path,remove_path,integrity
from .store import HygieneStore
from .final_recovery import policy_excluded,make_service

class CorpusHygieneService:
    def __init__(self,*,runtime_catalog,checkpoint_db,hygiene_db,recovery_db,work_dir):
        self.runtime_catalog=runtime_catalog; self.checkpoint_db=checkpoint_db
        self.store=HygieneStore(hygiene_db); self.recovery_db=recovery_db; self.work_dir=work_dir

    def audit(self):
        out=[]
        for r in failed_items(self.checkpoint_db):
            path=str(r["path"]); c,reason=classify_filesystem_artifact(path)
            if c is None and policy_excluded(path):
                c,reason="POLICY_EXCLUDED","Instructional weapon-conversion content excluded from recovery/indexing."
            if c is None:
                c,reason="LEGITIMATE_RESIDUAL_DOCUMENT","Eligible for final document-specific recovery."
            out.append({"candidate_id":str(r["candidate_id"]),"path":path,"classification":c,
                        "reason":reason,"runtime_present":has_path(self.runtime_catalog,path)})
        return out

    def apply_hygiene(self):
        results=[]
        for f in self.audit():
            if f["classification"] not in {"EXCLUDED_APPLEDOUBLE","EXCLUDED_FILESYSTEM_METADATA","POLICY_EXCLUDED"}:
                continue
            cleanup=remove_path(self.runtime_catalog,f["path"])
            stage="EXCLUDED_METADATA" if f["classification"].startswith("EXCLUDED_") else "EXCLUDED_POLICY"
            detail=f"Genesis X-A2.2: {f['classification']}. {f['reason']}"
            set_stage(self.checkpoint_db,f["candidate_id"],stage,detail)
            self.store.record(candidate_id=f["candidate_id"],path=f["path"],action="TERMINAL_EXCLUSION",
                              classification=f["classification"],detail=detail)
            results.append({"candidate_id":f["candidate_id"],"path":f["path"],"stage":stage,"cleanup":cleanup})
        return results

    def recover_final(self,limit=None):
        rows=[]
        for r in failed_items(self.checkpoint_db):
            path=str(r["path"]); c,_=classify_filesystem_artifact(path)
            if c or policy_excluded(path):continue
            rows.append(r)
        if limit is not None:rows=rows[:max(0,limit)]
        results=[]
        for r in rows:
            svc=make_service(self.runtime_catalog,self.checkpoint_db,self.recovery_db,self.work_dir,str(r["path"]))
            matches=[c for c in svc.candidates() if c.candidate_id==str(r["candidate_id"])]
            if not matches:continue
            cand=matches[0]
            outcome=svc.recover([cand],dry_run=False,writer_batch_size=1)[0]
            if outcome.status in {"RECOVERABLE_NATIVE","RECOVERABLE_OCR"}:
                self.store.record(candidate_id=cand.candidate_id,path=cand.path,action="RECOVERED",
                                  classification=outcome.status,detail=outcome.detail)
                results.append({"candidate_id":cand.candidate_id,"path":cand.path,"stage":"COMPLETE",
                                "detail":outcome.detail})
            else:
                detail=f"Genesis X-A2.2 final recovery exhausted: {outcome.status}: {outcome.detail}"
                set_stage(self.checkpoint_db,cand.candidate_id,"UNRECOVERABLE",detail)
                self.store.record(candidate_id=cand.candidate_id,path=cand.path,action="FINAL_UNRECOVERABLE",
                                  classification=outcome.status,detail=detail)
                results.append({"candidate_id":cand.candidate_id,"path":cand.path,"stage":"UNRECOVERABLE",
                                "detail":detail})
        return results

    def certify(self):
        rt=integrity(self.runtime_catalog); stages=stage_counts(self.checkpoint_db)
        incomplete=sum(int(stages.get(x,0)) for x in ("DISCOVERED","VALIDATED","EXTRACTING","EXTRACTED","CHUNKED","WRITING"))
        checks={"sqlite_integrity_ok":rt["integrity_check"].casefold()=="ok",
                "chunk_fts_parity":rt["chunk_fts_parity"],
                "no_duplicate_runtime_paths":rt["duplicate_runtime_paths"]==0,
                "no_orphan_chunks":rt["orphan_chunks"]==0,
                "no_incomplete_stages":incomplete==0,
                "no_failed_candidates":int(stages.get("FAILED",0))==0}
        return {"status":"EXCELLENT" if all(checks.values()) else "FAILED",
                "checks":checks,"runtime":rt,"stage_counts":stages,
                "hygiene_action_counts":self.store.counts()}

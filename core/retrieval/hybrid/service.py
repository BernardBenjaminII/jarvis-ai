from __future__ import annotations
import sqlite3, time
from pathlib import Path
from .dedup import duplicate_key
from .metadata import metadata_score
from .models import Candidate
from .query_analysis import analyze_query
from .semantic import SemanticAdapter

class HybridRetrievalService:
    def __init__(self, database: Path):
        self.database=Path(database)
        self.semantic=SemanticAdapter(self.database)

    def _connect(self):
        c=sqlite3.connect(f"file:{self.database.resolve()}?mode=ro",uri=True,timeout=30)
        c.row_factory=sqlite3.Row
        return c

    def lexical(self, query: str, limit: int=75):
        with self._connect() as c:
            rows=c.execute("""
              SELECT document_id,chunk_id,title,file_path,
                     bm25(runtime_chunks_fts) AS rank,
                     snippet(runtime_chunks_fts,0,'[',']',' … ',30) AS excerpt
              FROM runtime_chunks_fts
              WHERE runtime_chunks_fts MATCH ?
              ORDER BY rank LIMIT ?
            """,(query,limit)).fetchall()
        out=[]
        for pos,r in enumerate(rows,1):
            out.append(Candidate(
                document_id=str(r["document_id"]),chunk_id=str(r["chunk_id"]),
                title=str(r["title"]),file_path=str(r["file_path"]),
                excerpt=str(r["excerpt"]),bm25_rank=float(r["rank"]),
                lexical_rank_position=pos,
            ))
        return out

    @staticmethod
    def _rrf(rank: int | None, k: int=60):
        return 0.0 if rank is None else 1.0/(k+rank)

    def search(self, query: str, limit: int=10, candidate_limit: int=75,
               max_per_document: int=2, query_vector=None):
        started=time.perf_counter()
        analysis=analyze_query(query)
        lexical=self.lexical(query,candidate_limit)

        sem_scores={}
        if query_vector is not None and self.semantic.status()["available"]:
            sem=self.semantic.search(query_vector,candidate_limit)
            sem_scores={chunk_id:(score,pos) for pos,(chunk_id,score) in enumerate(sem,1)}

        ranked=[]
        for c in lexical:
            ms, authority=metadata_score(analysis,c.title,c.file_path)
            sem_score, sem_pos = sem_scores.get(c.chunk_id,(None,None))
            key=duplicate_key(c.title,c.excerpt)
            fused=(
                self._rrf(c.lexical_rank_position)
                + self._rrf(sem_pos)
                + 0.015*ms
                + 0.02*authority
                + (0.03*sem_score if sem_score is not None else 0.0)
            )
            ranked.append(Candidate(
                document_id=c.document_id,chunk_id=c.chunk_id,title=c.title,
                file_path=c.file_path,excerpt=c.excerpt,bm25_rank=c.bm25_rank,
                lexical_rank_position=c.lexical_rank_position,
                semantic_score=sem_score,semantic_rank_position=sem_pos,
                metadata_score=ms,fused_score=fused,
                provenance_score=authority,duplicate_key=key,
            ))

        ranked.sort(key=lambda x:x.fused_score,reverse=True)

        selected=[]
        per_doc={}
        seen_dupes=set()
        for c in ranked:
            if c.duplicate_key in seen_dupes:
                continue
            count=per_doc.get(c.document_id,0)
            if count>=max_per_document:
                continue
            selected.append(c)
            seen_dupes.add(c.duplicate_key)
            per_doc[c.document_id]=count+1
            if len(selected)>=limit:
                break

        return {
            "query":query,
            "analysis":analysis.to_dict(),
            "semantic":self.semantic.status(),
            "latency_ms":round((time.perf_counter()-started)*1000,2),
            "candidate_count":len(lexical),
            "results":[x.to_dict() for x in selected],
        }

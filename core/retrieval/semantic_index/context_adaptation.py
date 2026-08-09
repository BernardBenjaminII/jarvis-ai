from __future__ import annotations
import hashlib
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SemanticFragment:
    runtime_chunk_id:int
    fragment_index:int
    fragment_uuid:str
    start_char:int
    end_char:int
    text:str

def fragment_uuid(chunk_uuid:str, fragment_index:int, text:str)->str:
    h=hashlib.sha256(text.encode("utf-8",errors="ignore")).hexdigest()[:16]
    return f"{chunk_uuid}:{fragment_index}:{h}"

def split_text(text:str,*,target_chars:int=2200,overlap_chars:int=220,minimum_chars:int=200):
    n=len(text)
    if n<=target_chars:
        yield 0,n,text
        return
    cursor=0
    while cursor<n:
        hard=min(n,cursor+target_chars)
        if hard==n:
            end=n
        else:
            window=text[cursor:hard]
            cut=-1
            for sep in ("\n\n","\n",". ","; ",", "):
                pos=window.rfind(sep)
                if pos>=int(target_chars*0.60):
                    cut=pos+len(sep); break
            end=cursor+(cut if cut>0 else len(window))
        value=text[cursor:end].strip()
        if len(value)>=minimum_chars or cursor==0:
            yield cursor,end,value
        if end>=n: break
        cursor=max(cursor+1,end-overlap_chars)

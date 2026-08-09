from __future__ import annotations
import hashlib

def child_fragment_uuid(parent_uuid:str, child_index:int, text:str)->str:
    h=hashlib.sha256(text.encode('utf-8',errors='ignore')).hexdigest()[:16]
    return f"{parent_uuid}.{child_index}:{h}"

def split_leaf_text(text:str,*,target_chars:int=1400,overlap_chars:int=140,minimum_chars:int=160):
    n=len(text)
    if n<=target_chars:
        yield 0,n,text; return
    cursor=0
    while cursor<n:
        hard=min(n,cursor+target_chars)
        if hard==n: end=n
        else:
            window=text[cursor:hard]; cut=-1
            for sep in ('\n\n','\n','. ','; ',', ',' '):
                pos=window.rfind(sep)
                if pos>=int(target_chars*0.55): cut=pos+len(sep); break
            end=cursor+(cut if cut>0 else len(window))
        value=text[cursor:end].strip()
        if len(value)>=minimum_chars or cursor==0: yield cursor,end,value
        if end>=n: break
        cursor=max(cursor+1,end-overlap_chars)

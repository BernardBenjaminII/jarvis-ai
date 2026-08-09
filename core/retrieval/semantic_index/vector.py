from __future__ import annotations
from array import array
import hashlib, math

def pack_vector(values):
    a=array("f",(float(x) for x in values))
    raw=a.tobytes()
    return raw, len(a), hashlib.sha256(raw).hexdigest()

def unpack_vector(blob):
    a=array("f")
    a.frombytes(blob)
    return a

def cosine(a,b):
    if len(a)!=len(b): return None
    dot=sum(float(x)*float(y) for x,y in zip(a,b))
    na=math.sqrt(sum(float(x)*float(x) for x in a))
    nb=math.sqrt(sum(float(y)*float(y) for y in b))
    return (dot/(na*nb)) if na and nb else 0.0

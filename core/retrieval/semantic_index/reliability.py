import math,time,urllib.error
from dataclasses import dataclass

TRANSIENT_HTTP={408,425,429,500,502,503,504}

@dataclass(frozen=True)
class ProviderFailure(Exception):
    classification:str
    detail:str
    http_status:int|None=None
    body:str=""
    transient:bool=False
    def __str__(self): return self.detail

def classify_exception(exc):
    if isinstance(exc,ProviderFailure): return exc
    if isinstance(exc,urllib.error.HTTPError):
        try: body=exc.read().decode("utf-8",errors="replace")
        except Exception: body=""
        status=int(exc.code); transient=status in TRANSIENT_HTTP
        return ProviderFailure("TRANSIENT_PROVIDER" if transient else "HTTP_REJECTED",
            f"HTTPError {status}: {exc.reason}; body={body[:4000]}",
            status,body[:4000],transient)
    if isinstance(exc,urllib.error.URLError):
        return ProviderFailure("CONNECTION_FAILURE",f"URLError: {exc.reason}",None,"",True)
    if isinstance(exc,TimeoutError):
        return ProviderFailure("TIMEOUT",f"TimeoutError: {exc}",None,"",True)
    return ProviderFailure(type(exc).__name__.upper(),f"{type(exc).__name__}: {exc}")

def validate_vectors(vectors,expected_count,expected_dimensions=None):
    if not isinstance(vectors,list) or len(vectors)!=expected_count:
        raise ProviderFailure("VECTOR_COUNT_MISMATCH",f"Expected {expected_count}, got {len(vectors) if isinstance(vectors,list) else 'non-list'}")
    dims=None
    for i,v in enumerate(vectors):
        if not isinstance(v,list) or not v: raise ProviderFailure("INVALID_VECTOR",f"Embedding {i} invalid")
        dims=dims or len(v)
        if len(v)!=dims: raise ProviderFailure("DIMENSION_MISMATCH",f"Embedding {i} dimension mismatch")
        if expected_dimensions is not None and len(v)!=expected_dimensions:
            raise ProviderFailure("DIMENSION_MISMATCH",f"Embedding {i} dimension {len(v)} != {expected_dimensions}")
        for x in v:
            if not math.isfinite(float(x)): raise ProviderFailure("INVALID_VECTOR",f"Embedding {i} contains non-finite value")
    return dims or 0

def backoff_seconds(attempt): return min(2.0,0.15*(2**max(0,attempt-1)))

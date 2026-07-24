from __future__ import annotations
from dataclasses import asdict, is_dataclass
from hashlib import sha256
from typing import Any, Mapping, Protocol, Sequence
from .policies import IntegrityPolicy
from .reports import IntegrityCode, IntegrityObservation, canonical_json, fingerprint

class CheckpointRepositoryProtocol(Protocol):
    def history(self, session_id:str)->Sequence[Any]: ...

def read(obj,*names,default=None):
    for name in names:
        if isinstance(obj,Mapping) and name in obj: return obj[name]
        if hasattr(obj,name): return getattr(obj,name)
    return default

def mapping(obj):
    if isinstance(obj,Mapping): return dict(obj)
    if hasattr(obj,'canonical_dict'): return dict(obj.canonical_dict())
    if is_dataclass(obj): return asdict(obj)
    if hasattr(obj,'to_dict'): return dict(obj.to_dict())
    if hasattr(obj,'__dict__'): return dict(vars(obj))
    raise TypeError(f'Unsupported checkpoint: {type(obj)!r}')

def seq(c):
    raw=read(c,'sequence','sequence_number','ordinal','index')
    try: return int(raw)
    except (TypeError,ValueError): return None

def cid(c):
    raw=read(c,'checkpoint_id','id','record_id'); return None if raw is None else str(raw)
def cdigest(c):
    raw=read(c,'checkpoint_digest','digest','fingerprint','integrity_digest'); return None if raw is None else str(raw)
def parent(c):
    raw=read(c,'parent_digest','previous_digest','parent_checkpoint_digest','previous_checkpoint_digest'); return None if raw in (None,'') else str(raw)
def schema(c):
    raw=read(c,'schema','schema_name','schema_version'); return None if raw is None else str(raw)
def payload(c): return read(c,'payload','snapshot','state','serialized_snapshot')
def pdigest(c):
    raw=read(c,'payload_digest','snapshot_digest','payload_fingerprint'); return None if raw is None else str(raw)
def hash_payload(value):
    data=value if isinstance(value,bytes) else (value.encode() if isinstance(value,str) else canonical_json(value).encode())
    return sha256(data).hexdigest()
def hash_checkpoint(c):
    m=mapping(c)
    for key in ('checkpoint_digest','digest','fingerprint','integrity_digest'): m.pop(key,None)
    return sha256(canonical_json(m).encode()).hexdigest()

class IntegrityScanner:
    def __init__(self, repository, *, policy=None):
        self.repository=repository; self.policy=policy or IntegrityPolicy()
    def scan_session(self, session_id):
        try: checkpoints=tuple(self.repository.history(session_id))
        except Exception as exc:
            obs=IntegrityObservation(IntegrityCode.REPOSITORY_ERROR,session_id,detail=f'{type(exc).__name__}: {exc}')
            return (), (obs,), fingerprint([])
        if not checkpoints:
            return (), (IntegrityObservation(IntegrityCode.EMPTY_SESSION,session_id,detail='No checkpoints found.'),), fingerprint([])
        observations=[]; indexed=[]
        for c in checkpoints:
            s=seq(c)
            if s is None:
                observations.append(IntegrityObservation(IntegrityCode.INVALID_SEQUENCE,session_id,cid(c),detail='Sequence missing or invalid.'))
            else: indexed.append((s,c))
        indexed.sort(key=lambda x:(x[0],cid(x[1]) or ''))
        expected=self.policy.sequence_origin; seen=set(); previous=None
        for s,c in indexed:
            if s in seen: observations.append(IntegrityObservation(IntegrityCode.DUPLICATE_SEQUENCE,session_id,cid(c),s,actual=s,detail='Duplicate sequence.'))
            seen.add(s)
            if s != expected:
                observations.append(IntegrityObservation(IntegrityCode.SEQUENCE_GAP,session_id,cid(c),s,expected,s,'Sequence discontinuity.'))
                expected=s
            expected += 1
            actual_parent=parent(c)
            if previous is None and actual_parent is not None:
                observations.append(IntegrityObservation(IntegrityCode.PARENT_MISMATCH,session_id,cid(c),s,None,actual_parent,'First checkpoint has a parent.'))
            elif previous is not None and actual_parent != previous:
                observations.append(IntegrityObservation(IntegrityCode.PARENT_MISMATCH,session_id,cid(c),s,previous,actual_parent,'Parent digest mismatch.'))
            if not self.policy.schema_supported(schema(c)):
                observations.append(IntegrityObservation(IntegrityCode.UNSUPPORTED_SCHEMA,session_id,cid(c),s,','.join(sorted(self.policy.supported_schemas)),schema(c),'Unsupported schema.'))
            p=payload(c); declared=pdigest(c)
            if p is not None and declared is not None:
                actual=hash_payload(p)
                if actual != declared: observations.append(IntegrityObservation(IntegrityCode.PAYLOAD_DIGEST_MISMATCH,session_id,cid(c),s,declared,actual,'Payload digest mismatch.'))
            declared_checkpoint=cdigest(c)
            if declared_checkpoint is not None:
                try: actual_checkpoint=hash_checkpoint(c)
                except Exception as exc: observations.append(IntegrityObservation(IntegrityCode.MALFORMED_CHECKPOINT,session_id,cid(c),s,detail=f'{type(exc).__name__}: {exc}'))
                else:
                    if actual_checkpoint != declared_checkpoint: observations.append(IntegrityObservation(IntegrityCode.CHECKPOINT_DIGEST_MISMATCH,session_id,cid(c),s,declared_checkpoint,actual_checkpoint,'Checkpoint digest mismatch.'))
            previous=declared_checkpoint
        items=[{'sequence':s,'checkpoint_id':cid(c),'checkpoint_digest':cdigest(c),'parent_digest':parent(c)} for s,c in indexed]
        return tuple(c for _,c in indexed), tuple(observations), fingerprint(items)

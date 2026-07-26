from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from .errors import ObservationConvergenceError
PATTERN=re.compile(r"^\s*class\s+Observation(?:\s*[\(:])",re.MULTILINE)
ALLOWED={"core/cognition/contracts.py","core/cognition/observation.py"}
@dataclass(frozen=True,slots=True)
class ObservationDefinition: path:str; canonical:bool; legacy_allowed:bool
@dataclass(frozen=True,slots=True)
class ObservationConvergenceReport:
    repository_root:str; canonical_path:str; definitions:tuple[ObservationDefinition,...]; forbidden_duplicates:tuple[str,...]; fingerprint:str
    @property
    def converged(self): return not self.forbidden_duplicates
def audit_observation_definitions(repository_root):
    root=Path(repository_root).resolve(); canonical="core/observation/contracts.py"; defs=[]
    for p in sorted((root/"core").rglob("*.py")):
        if "__pycache__" in p.parts: continue
        rel=p.relative_to(root).as_posix()
        if PATTERN.search(p.read_text(encoding="utf-8",errors="ignore")): defs.append(ObservationDefinition(rel,rel==canonical,rel in ALLOWED))
    forbidden=tuple(x.path for x in defs if not x.canonical and not x.legacy_allowed)
    fp=sha256("|".join(f"{x.path}:{x.canonical}:{x.legacy_allowed}" for x in defs).encode()).hexdigest()
    return ObservationConvergenceReport(str(root),canonical,tuple(defs),forbidden,fp)
def require_observation_convergence(repository_root):
    report=audit_observation_definitions(repository_root)
    if not report.converged: raise ObservationConvergenceError("forbidden Observation definitions: "+", ".join(report.forbidden_duplicates))
    return report

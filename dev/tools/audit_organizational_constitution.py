#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

TERMS=("organization","organizational","department","directorate","bureau","service","campaign","authority","reporting chain","chain of command","governance","executive director","director registry","mission control")
ROOTS=("docs/constitution","docs/architecture","docs/decisions","core/executive","core/src/routes","core/src/static/mission_control")
SUFFIXES={".md",".txt",".py",".json",".yaml",".yml",".toml",".html",".js",".css"}

@dataclass(frozen=True, slots=True)
class Hit:
    path:str; line:int; term:str; excerpt:str


def files(root:Path):
    for rel in ROOTS:
        p=root/rel
        if not p.exists(): continue
        if p.is_file(): yield p; continue
        for f in sorted(p.rglob('*')):
            if f.is_file() and f.suffix.lower() in SUFFIXES and '__pycache__' not in f.parts:
                yield f


def scan(root:Path):
    hits=[]
    for path in files(root):
        try: lines=path.read_text(encoding='utf-8',errors='replace').splitlines()
        except OSError: continue
        for n,line in enumerate(lines,1):
            low=line.lower()
            for term in TERMS:
                if term in low:
                    hits.append(Hit(path.relative_to(root).as_posix(),n,term,re.sub(r'\s+',' ',line.strip())[:240]))
    return tuple(sorted(hits,key=lambda h:(h.path,h.line,h.term)))


def classify(hits):
    paths=sorted({h.path for h in hits})
    exact=tuple(p for p in paths if Path(p).name.lower() in {'organization.md','organizational_constitution.md','organization_constitution.md','goa-0000.md'})
    constitutional=tuple(p for p in paths if p.startswith('docs/constitution/'))
    architecture=tuple(p for p in paths if p.startswith('docs/architecture/') or p.startswith('docs/decisions/'))
    implementation=tuple(p for p in paths if p.startswith('core/executive/'))
    mission=tuple(p for p in paths if p.startswith('core/src/routes/') or p.startswith('core/src/static/mission_control/'))
    status='already_exists' if exact else ('partially_exists' if constitutional or architecture or implementation else 'does_not_exist')
    payload={'classification':status,'exact_constitution_found':bool(exact),'constitutional_sources':constitutional,'architecture_sources':architecture,'implementation_sources':implementation,'mission_control_sources':mission,'hits':[asdict(h) for h in hits]}
    payload['fingerprint']=sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return payload


def write_md(report,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    lines=['# Genesis VII-C0A-1 — Organizational Constitution Audit','',f"**Classification:** `{report['classification']}`  ",f"**Exact constitution found:** `{report['exact_constitution_found']}`  ",f"**Fingerprint:** `{report['fingerprint']}`",'', '## Interpretation','']
    msg={'already_exists':'A canonical organizational constitution appears to already exist. Certify or consolidate it rather than replacing it.','partially_exists':'Organizational doctrine and implementation exist in fragments, but no canonical constitution was identified. Consolidate existing sources.','does_not_exist':'No meaningful organizational constitutional foundation was identified.'}[report['classification']]
    lines.append(msg)
    for title,key in [('Constitutional sources','constitutional_sources'),('Architecture and ADR sources','architecture_sources'),('Executive implementation sources','implementation_sources'),('Mission Control and route sources','mission_control_sources')]:
        lines+=['',f'## {title}','']
        vals=report[key]; lines += [f'- `{v}`' for v in vals] if vals else ['- None discovered.']
    lines+=['','## Matched evidence','']
    lines += [f"- `{h['path']}:{h['line']}` — **{h['term']}** — {h['excerpt']}" for h in report['hits']]
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',default='.'); ap.add_argument('--json-output',default='artifacts/audit/genesis_vii_c0a1_organizational_constitution.json'); ap.add_argument('--markdown-output',default='artifacts/audit/genesis_vii_c0a1_organizational_constitution.md'); a=ap.parse_args()
    root=Path(a.project_root).resolve(); report=classify(scan(root))
    jp=root/a.json_output; jp.parent.mkdir(parents=True,exist_ok=True); jp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    mp=root/a.markdown_output; write_md(report,mp)
    print('='*72); print('JARVIS — GENESIS VII-C0A-1'); print('ORGANIZATIONAL CONSTITUTION AUDIT'); print('='*72); print('Classification      :',report['classification'].upper()); print('Exact constitution  :',report['exact_constitution_found']); print('Evidence hits       :',len(report['hits'])); print('Fingerprint         :',report['fingerprint']); print('JSON report         :',jp); print('Markdown report     :',mp); print('='*72)
    return 0
if __name__=='__main__': raise SystemExit(main())

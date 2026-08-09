from __future__ import annotations

import textwrap
import ast, inspect
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

@dataclass(frozen=True, slots=True)
class CallableRecord:
    owner:str; attribute:str; module:str|None; qualname:str|None; signature:str|None; source_file:str|None; source_line:int|None; public:bool; bound:bool
    def to_dict(self): return asdict(self)

class ExecutiveRuntimeCallGraphReconstructor:
    def __init__(self, repository_root:Path): self.root=repository_root.resolve()
    def reconstruct(self):
        from core.src.routes.api import conversation_service
        orchestrator=getattr(conversation_service,'orchestrator',None)
        owners={
          'conversation_service':conversation_service,
          'orchestrator':orchestrator,
          'director':getattr(orchestrator,'director',None) if orchestrator else None,
          'grounding_service':getattr(orchestrator,'grounding_service',None) if orchestrator else None,
          'awareness_service':getattr(orchestrator,'awareness_service',None) if orchestrator else None,
        }
        callables=[r for name,obj in owners.items() for r in self._callables(name,obj)]
        flow=self._orchestrator_flow(orchestrator)
        director_methods=[r for r in callables if r.owner=='director' and r.public]
        hook=self._select_hook(owners['director'],director_methods,flow)
        edges=self._edges(owners,flow)
        verdict=self._verdict(owners['director'],hook,flow)
        return {
          'schema_version':'genesis_ix_a4_3c_v1','generated_at':datetime.now(timezone.utc).isoformat(),'repository_root':str(self.root),
          'objects':{k:self._identity(v) for k,v in owners.items()},'callables':[x.to_dict() for x in callables],
          'director_methods':[x.to_dict() for x in director_methods],'director_hook':hook,'orchestrator_flow':flow,
          'edges':edges,'verdict':verdict,'ix_a4_3b_repair_contract':self._repair(hook,flow),
        }
    def _identity(self,v):
        return None if v is None else {'module':type(v).__module__,'type':type(v).__name__,'qualified_type':f'{type(v).__module__}.{type(v).__name__}'}
    def _callables(self,owner_name,obj):
        if obj is None:return []
        out=[]
        for name in dir(obj):
            if name.startswith('__') and name.endswith('__'):continue
            try:value=getattr(obj,name)
            except Exception:continue
            if not callable(value):continue
            try:sig=str(inspect.signature(value))
            except Exception:sig=None
            try:file=inspect.getsourcefile(value)
            except Exception:file=None
            try:line=inspect.getsourcelines(value)[1]
            except Exception:line=None
            out.append(CallableRecord(owner_name,name,getattr(value,'__module__',None),getattr(value,'__qualname__',None),sig,file,line,not name.startswith('_'),getattr(value,'__self__',None) is obj))
        return sorted(out,key=lambda x:(x.owner,not x.public,x.attribute))
    def _orchestrator_flow(self,orchestrator):
        if orchestrator is None:return {'status':'absent','entry_method':None,'calls':[]}
        entry=getattr(orchestrator,'execute',None)
        if not callable(entry):
            public=[n for n in dir(orchestrator) if not n.startswith('_') and callable(getattr(orchestrator,n,None))]
            return {'status':'entry_unresolved','entry_method':None,'public_methods':sorted(public),'calls':[]}
        try:src=inspect.getsource(entry); file=inspect.getsourcefile(entry); start=inspect.getsourcelines(entry)[1]
        except Exception as exc:return {'status':'source_unavailable','entry_method':'execute','error':f'{type(exc).__name__}: {exc}','calls':[]}
        tree=ast.parse(textwrap.dedent(src)); calls=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                try:target=ast.unparse(node.func)
                except Exception:target='<unknown>'
                if any(t in target for t in ('ground','assess','director','synthesis','compile','observe','plan','route','dispatch')):
                    calls.append({'target':target,'absolute_line':start+getattr(node,'lineno',1)-1})
        return {'status':'resolved','entry_method':'execute','source_file':file,'source_line':start,'calls':calls,'director_referenced':any('director' in x['target'] for x in calls)}
    def _select_hook(self,director,methods,flow):
        if director is None:return {'status':'absent','method':None,'reason':'No Director injected.'}
        references=' '.join(x.get('target','') for x in flow.get('calls',[]))
        priority={'direct':100,'dispatch':95,'route':90,'plan':85,'decide':80,'coordinate':75,'handle':70,'process':65,'run':60,'invoke':55,'execute':50}
        ranked=[]
        for m in methods:
            score=priority.get(m.attribute.casefold(),0); reasons=[]
            if score:reasons.append(f'semantic priority={score}')
            if f'director.{m.attribute}' in references:score+=50; reasons.append('referenced by orchestrator')
            if m.signature and m.signature not in ('()','(self)'):score+=10; reasons.append('accepts runtime input')
            ranked.append((score,m,reasons))
        ranked.sort(key=lambda x:(x[0],x[1].attribute),reverse=True)
        if not ranked or ranked[0][0]<=0:return {'status':'not_invoked','method':None,'reason':'No public Director callable is referenced by the live flow.','candidates':[m.to_dict() for m in methods]}
        score,m,reasons=ranked[0]
        return {'status':'resolved','method':m.attribute,'qualified_name':m.qualname,'module':m.module,'signature':m.signature,'source_file':m.source_file,'source_line':m.source_line,'score':score,'reasons':reasons,'candidates':[{'method':x.attribute,'score':s,'reasons':r} for s,x,r in ranked[:10]]}
    def _edges(self,owners,flow):
        edges=[]
        if owners['conversation_service'] and owners['orchestrator']:edges.append({'source':'conversation_service','target':'orchestrator','relation':'owns','evidence':'conversation_service.orchestrator'})
        if owners['orchestrator']:
            for attr in ('director','grounding_service','awareness_service','observability_service','synthesis_handler'):
                if getattr(owners['orchestrator'],attr,None) is not None:edges.append({'source':'orchestrator','target':attr,'relation':'owns','evidence':f'orchestrator.{attr}'})
        for call in flow.get('calls',[]):edges.append({'source':'orchestrator.execute','target':call['target'],'relation':'source_call','evidence':f"{flow.get('source_file')}:{call.get('absolute_line')}"})
        return edges
    def _verdict(self,director,hook,flow):
        if director is None:return {'classification':'CONFIGURATION_DEFECT','reason':'No ExecutiveDirector is injected.','blocking':True}
        if flow.get('status')!='resolved':return {'classification':'CALL_GRAPH_UNRESOLVED','reason':'Orchestrator entry method could not be reconstructed.','blocking':True}
        if not flow.get('director_referenced'):return {'classification':'DIRECTOR_NOT_IN_EXECUTION_PATH','reason':'ExecutiveDirector is injected but not called by orchestrator.execute; IX-A4.3B must not patch director.execute.','blocking':False}
        if hook.get('status')=='resolved':return {'classification':'DIRECTOR_HOOK_RESOLVED','reason':f"Actual Director hook is {hook.get('method')!r}.",'blocking':False}
        return {'classification':'DIRECTOR_REFERENCE_UNRESOLVED','reason':'Orchestrator references Director but exact callable is unresolved.','blocking':True}
    def _repair(self,hook,flow):
        if not flow.get('director_referenced'):return {'action':'remove_director_patch','instructions':'Trace orchestrator.execute, grounding_service.ground, awareness_service.assess, synthesis_handler, and conversation response. Do not access director.execute.'}
        if hook.get('status')=='resolved':return {'action':'patch_resolved_director_method','method':hook.get('method'),'instructions':'Replace hard-coded director.execute with the resolved callable and guard with callable inspection.'}
        return {'action':'trace_orchestrator_only','instructions':'Instrument orchestrator source-call boundaries instead of mutating Director.'}

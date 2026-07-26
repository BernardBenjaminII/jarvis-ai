from dataclasses import replace
from pathlib import Path
import hashlib
from .contracts import IntegrationFinding, IntegrationHealthProjection, IntegrationLink, utc_now_iso
from .enums import CapabilityLifecycle as L, HealthStatus as H, IntegrationStatus as I, Severity as S, VisibilitySurface as V
from .projections import build_capability_projection, determine_overall_health
from .registry import CapabilityRegistry

PATHS={'observation':('core/observation','core/cognition/observation'),'situation':('core/cognition','core/situation'),'hypothesis':('core/cognition','core/reasoning'),'evidence':('core/evidence',),'reasoning':('core/reasoning',),'decision':('core/cognition/executive_decision','core/cognition/decision'),'mission_compiler':('core/cognition/mission_compiler',),'execution_orchestrator':('core/cognition/execution_orchestrator',),'knowledge_catalog':('core/knowledge','core/knowledge_catalog'),'acquisition':('core/acquisition',),'executive_api':('core/src/routes',),'mission_control_ui':('ui','frontend','web')}
class RepositoryIntegrationAuditor:
    def audit(self, repository_root: Path, registry: CapabilityRegistry):
        root=repository_root.resolve(); enriched=CapabilityRegistry(); findings=[]
        for c in registry.all():
            found=tuple(p for p in PATHS.get(c.capability_id,()) if (root/p).exists())
            lifecycle,health=c.lifecycle,c.health
            if found:
                if lifecycle in {L.PLANNED,L.NOT_CONNECTED} and c.capability_id not in {'executive_api','mission_control_ui'}: lifecycle=L.IMPLEMENTED
                health=H.HEALTHY
            else:
                lifecycle=L.UNAVAILABLE if lifecycle is not L.PLANNED else lifecycle; health=H.UNAVAILABLE
                findings.append(self._finding(c.capability_id,V.RUNTIME,S.CRITICAL,'Canonical implementation path was not discovered.','Confirm the canonical owner path or install the capability.'))
            api=self._discover(root/'core/src/routes',root,c.capability_id)
            ui=tuple(sorted(set(self._discover(root/'ui',root,c.capability_id)+self._discover(root/'frontend',root,c.capability_id)+self._discover(root/'web',root,c.capability_id))))
            vis=set(c.visibility)
            if api: vis.add(V.API)
            if ui: vis.add(V.UI)
            if c.capability_id not in {'executive_api','mission_control_ui'} and not api: findings.append(self._finding(c.capability_id,V.API,S.WARNING,'Capability is not projected by the Executive API audit.','Add or map a read-only Executive API projection.'))
            if c.capability_id not in {'executive_api','mission_control_ui'} and not ui: findings.append(self._finding(c.capability_id,V.UI,S.WARNING,'Capability is not represented in Mission Control.','Add or map a Mission Control surface.'))
            enriched.upsert(replace(c,lifecycle=lifecycle,health=health,api_routes=api or c.api_routes,ui_surfaces=ui or c.ui_surfaces,visibility=tuple(sorted(vis,key=lambda x:x.value)),metadata={'discovered_paths':','.join(found)}))
        links=[]
        for target in enriched.all():
            for source_id in target.dependencies:
                source=enriched.get(source_id)
                if H.UNAVAILABLE in {source.health,target.health}: status=I.UNAVAILABLE
                elif L.NOT_CONNECTED in {source.lifecycle,target.lifecycle}: status=I.NOT_CONNECTED
                elif H.DEGRADED in {source.health,target.health}: status=I.DEGRADED
                else: status=I.CONNECTED
                links.append(IntegrationLink(source_id,target.capability_id,status,'contract',','.join(source.output_contracts) or 'unspecified',V.TELEMETRY in source.visibility or V.API in source.visibility))
        caps=tuple(build_capability_projection(x) for x in enriched.all())
        totals={'capabilities':str(len(caps)),'healthy':str(sum(x.health is H.HEALTHY for x in caps)),'unavailable':str(sum(x.health is H.UNAVAILABLE for x in caps)),'findings':str(len(findings))}
        return IntegrationHealthProjection(utc_now_iso(),determine_overall_health(caps),caps,tuple(sorted(links,key=lambda x:(x.source_capability,x.target_capability))),tuple(findings),totals)
    def _discover(self, base, root, token):
        if not base.exists(): return ()
        tokens={token,token.replace('_',' '),token.replace('_','-')}; out=set()
        for p in base.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.py','.js','.jsx','.ts','.tsx','.html','.css','.md'}:
                text=p.read_text(encoding='utf-8',errors='ignore').lower()
                if any(t.lower() in text for t in tokens): out.add(str(p.relative_to(root)))
        return tuple(sorted(out))
    def _finding(self,c,surface,severity,summary,recommendation):
        fid='finding-'+hashlib.sha256('|'.join((c,surface.value,severity.value,summary)).encode()).hexdigest()[:20]
        return IntegrationFinding(fid,severity,c,surface,summary,recommendation)

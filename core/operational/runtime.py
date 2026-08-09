from pathlib import Path
import json, threading
from core.government import GovernmentQuery, LifecycleState, bootstrap_government
from .models import BootCheck, OperationalSnapshot

class ExecutiveRuntime:
    def __init__(self,heartbeat_seconds=1.0,state_path='artifacts/runtime/jarvis_operational_state.json'):
        if heartbeat_seconds<=0: raise ValueError('heartbeat_seconds must be positive')
        self.heartbeat_seconds=heartbeat_seconds; self.state_path=Path(state_path); self.registry=None; self._cycle=0; self._running=False; self._stop=threading.Event(); self._checks=(); self._last=None
    @property
    def running(self): return self._running
    @property
    def last_snapshot(self): return self._last
    def boot(self):
        result=bootstrap_government(); self.registry=result.registry; self._running=True; self._stop.clear(); self._checks=(BootCheck('Constitution','PASS','GOA-0000'),BootCheck('Government','PASS',f'{result.object_count} objects / {result.relationship_count} relationships'),BootCheck('Registry','PASS',result.fingerprint),BootCheck('Executive Runtime','PASS','heartbeat initialized')); return self.run_cycle()
    def run_cycle(self):
        if self.registry is None: raise RuntimeError('runtime must be booted')
        self._cycle+=1; snap=self.registry.query(GovernmentQuery()); count=len(snap.objects); active=sum(1 for x in snap.objects if x.lifecycle is LifecycleState.ACTIVE); readiness=round(active/count*100) if count else 0
        result=OperationalSnapshot(self._cycle,'running' if self._running else 'stopped',self.registry.fingerprint(),count,len(snap.relationships),readiness,'healthy' if readiness==100 else 'degraded',self._checks,{'heartbeat_seconds':str(self.heartbeat_seconds),'active_objects':str(active)})
        self._last=result; self._publish(result); return result
    def run(self,cycles=None,on_cycle=None):
        if self.registry is None:self.boot()
        completed=0
        while self._running and not self._stop.is_set():
            if cycles is not None and completed>=cycles: break
            s=self.run_cycle(); completed+=1
            if on_cycle:on_cycle(s)
            if cycles is None or completed<cycles:self._stop.wait(self.heartbeat_seconds)
        return self._last
    def command(self,name):
        name=name.strip().lower().replace('-','_')
        if name=='reload_registry': self.registry=bootstrap_government().registry; return self.run_cycle()
        if name=='take_snapshot': self.registry.snapshot(f'runtime-cycle-{self._cycle}'); return self.run_cycle()
        if name=='show_health': return self.run_cycle()
        if name=='stop': self.stop(); return self._last
        raise ValueError(f'unknown Executive runtime command: {name}')
    def stop(self): self._running=False; self._stop.set(); self.run_cycle() if self.registry else None
    def _publish(self,s):
        self.state_path.parent.mkdir(parents=True,exist_ok=True); tmp=self.state_path.with_suffix(self.state_path.suffix+'.tmp'); tmp.write_text(json.dumps(s.to_dict(),indent=2,sort_keys=True)+'\n'); tmp.replace(self.state_path)

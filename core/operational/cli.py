import argparse, json
from .runtime import ExecutiveRuntime

def main():
    p=argparse.ArgumentParser(); p.add_argument('--heartbeat',type=float,default=1.0); p.add_argument('--cycles',type=int); p.add_argument('--state-path',default='artifacts/runtime/jarvis_operational_state.json'); p.add_argument('--command',choices=('reload_registry','take_snapshot','show_health','stop')); a=p.parse_args()
    r=ExecutiveRuntime(a.heartbeat,a.state_path); s=r.boot()
    for c in s.checks: print(f'{c.name:.<32} {c.status}')
    print('\nJARVIS READY')
    if a.command: print(json.dumps(r.command(a.command).to_dict(),indent=2,sort_keys=True)); return 0
    r.run(cycles=a.cycles,on_cycle=lambda x:print(f'[cycle={x.cycle}] health={x.health} readiness={x.readiness_percent}% objects={x.object_count} relationships={x.relationship_count}')); return 0

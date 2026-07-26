import argparse, json
from pathlib import Path
from .service import ExecutiveIntegrationService
from .serialization import to_canonical_data

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest='command',required=True); a=s.add_parser('audit'); a.add_argument('--repository-root',default='.'); a.add_argument('--output',default='docs/audits/genesis_iv_b1_integration_audit.json'); args=p.parse_args()
    root=Path(args.repository_root).resolve(); out=Path(args.output); out=out if out.is_absolute() else root/out; out.parent.mkdir(parents=True,exist_ok=True)
    projection=ExecutiveIntegrationService(root).integration_health(); out.write_text(json.dumps(to_canonical_data(projection),indent=2,sort_keys=True)+'
',encoding='utf-8')
    print(f'[PASS] Integration audit written: {out}'); print(f'[INFO] Overall health: {projection.overall_health.value}'); print(f'[INFO] Findings: {len(projection.findings)}')
if __name__=='__main__': main()

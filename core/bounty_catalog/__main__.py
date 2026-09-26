import argparse
import json
import os
from pathlib import Path
import tempfile
import time
from .hackerone import Client, DiscoveryError, MAX_BYTES, decode
from .store import Catalog, discover
from . import credentials


def main():
    parser = argparse.ArgumentParser(description='R4 read-only bounty opportunity catalog')
    parser.add_argument('--db', type=Path, default=Path(os.environ.get('JARVIS_RUNTIME_ROOT', str(Path.home()/'.local/share/jarvis')))/'bounty_catalog/r4.sqlite')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    auth = sub.add_parser('auth', help='Manage saved local API credentials')
    auth.add_argument('action', choices=('configure', 'status', 'forget'))
    live = sub.add_parser('discover')
    live.add_argument('--max-pages', type=int, choices=range(1,21), default=5)
    imp = sub.add_parser('import-json')
    imp.add_argument('file', type=Path)
    for name in ('list', 'proposal'):
        command = sub.add_parser(name)
        command.add_argument('--source', choices=('hackerone-api','hackerone-import'), default='hackerone-api')
        if name == 'list':
            command.add_argument('--paid-only', action='store_true')
        else:
            command.add_argument('handle')
    args = parser.parse_args()
    if args.command == 'auth':
        if args.action == 'configure':
            credentials.save(*credentials.prompt())
            result = {'credentials_saved': True, 'encrypted': False}
        elif args.action == 'forget':
            credentials.forget()
            result = {'local_credentials_removed': True, 'remote_token_revoked': False}
        else:
            result = {'credentials_saved': credentials.load() is not None, 'encrypted': False}
        print(json.dumps(result, indent=2))
        return 0
    if args.command == 'demo':
        # Synthetic observations never enter the real catalog.
        with tempfile.TemporaryDirectory(prefix='jarvis-catalog-demo-') as tmp:
            catalog = Catalog(Path(tmp)/'demo.sqlite')
            raw = json.dumps({'data': [
                {'type':'program','attributes':{'handle':'jarvis-demo-paid','name':'Synthetic Paid Program','offers_bounties':True,'submission_state':'open'}},
                {'type':'program','attributes':{'handle':'jarvis-demo-vdp','name':'Synthetic Disclosure Program','offers_bounties':False}},
                {'type':'program','attributes':{'handle':'jarvis-demo-unknown','name':'Synthetic Unknown Program'}}], 'links':{}}).encode()
            catalog.save('synthetic-demo', time.time(), [(1,raw,time.time())], 'synthetic')
            all_rows = catalog.list(source='synthetic-demo')['programs']
            paid = catalog.list(source='synthetic-demo', paid_only=True)['programs']
            proposal = catalog.proposal('jarvis-demo-paid', source='synthetic-demo')
            result = {'mode':'synthetic_catalog_demo', 'passed':len(all_rows)==3 and len(paid)==1 and proposal['execution_enabled'] is False,
                      'programs':len(all_rows), 'paid_programs':len(paid), 'network_requests':0,
                      'real_catalog_modified':False, 'proposal_state':proposal['state'], 'execution_enabled':False}
    else:
        catalog = Catalog(args.db)
        if args.command == 'discover':
            username, token = credentials.resolve()
            client = Client(username, token)
            result = discover(catalog, client, args.max_pages)
            del token, client
        elif args.command == 'import-json':
            with args.file.open('rb') as stream:
                raw = stream.read(MAX_BYTES + 1)
            decode(raw)
            result = catalog.save('hackerone-import', time.time(), [(1,raw,time.time())], 'local_import_unverified')
        elif args.command == 'list':
            result = catalog.list(source=args.source, paid_only=args.paid_only)
        else:
            result = catalog.proposal(args.handle, source=args.source)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 1 if result.get('status') == 'error' or result.get('passed') is False else 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (DiscoveryError, OSError) as exc:
        raise SystemExit('Catalog error: ' + str(exc)) from None

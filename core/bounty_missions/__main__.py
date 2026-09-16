import argparse
import json
import os
from pathlib import Path
from .engine import Store

parser = argparse.ArgumentParser(description='Persistent owned-loopback fixture only')
parser.add_argument('--db', type=Path, default=Path(os.environ.get('JARVIS_RUNTIME_ROOT', str(Path.home()/'.local/share/jarvis')))/'bounty_missions/r3.sqlite')
commands = parser.add_subparsers(dest='command', required=True)
commands.add_parser('demo')
for name in ('report', 'cancel'):
    command = commands.add_parser(name)
    command.add_argument('mission')
args = parser.parse_args()
store = Store(args.db)
if args.command == 'demo':
    mid = store.create(['*.example.test'], ['private.example.test'], budget=1)
    store.review(mid, 'built-in owned-loopback lab demo')
    tid = store.queue(mid, 'www.example.test')
    evidence = store.run(mid, tid)
    print(json.dumps(store.report(mid), indent=2))
    raise SystemExit(0 if evidence['state'] == 'completed' else 1)
if args.command == 'cancel':
    store.cancel(args.mission)
print(json.dumps(store.report(args.mission), indent=2))

import argparse
import json
import os
from pathlib import Path
from .engine import Store, Denied


def main():
    parser = argparse.ArgumentParser(description='Jarvis bounty R1 — synthetic laboratory only')
    parser.add_argument('--db', default=str(Path(os.environ.get('JARVIS_RUNTIME_ROOT',
                        Path.home() / '.local/share/jarvis')) / 'bounty_lab/missions.sqlite'))
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('create')
    p.add_argument('--include', action='append', required=True)
    p.add_argument('--exclude', action='append', default=[])
    p.add_argument('--budget', type=int, default=5)
    p.add_argument('--ttl', type=int, default=3600)
    p = sub.add_parser('review-lab')
    p.add_argument('mission'); p.add_argument('--reviewer', required=True)
    p = sub.add_parser('queue'); p.add_argument('mission'); p.add_argument('target')
    p = sub.add_parser('run'); p.add_argument('mission'); p.add_argument('task')
    for name in ('report', 'cancel'):
        sub.add_parser(name).add_argument('mission')
    sub.add_parser('demo')
    args = parser.parse_args()
    store = Store(args.db)
    try:
        if args.command == 'create':
            out = {'mission_id': store.create(args.include, args.exclude, args.budget, args.ttl)}
        elif args.command == 'review-lab':
            store.review(args.mission, args.reviewer); out = {'state': 'ready'}
        elif args.command == 'queue':
            out = {'task_id': store.queue(args.mission, args.target)}
        elif args.command == 'run':
            out = store.run(args.mission, args.task)
        elif args.command == 'report':
            out = store.report(args.mission)
        elif args.command == 'cancel':
            store.cancel(args.mission); out = {'state': 'cancelled'}
        else:
            mid = store.create(['*.example.test'], ['private.example.test'], budget=1)
            store.review(mid, 'built-in synthetic demo')
            tid = store.queue(mid, 'www.example.test')
            store.run(mid, tid)
            out = store.report(mid)
            try:
                store.queue(mid, 'private.example.test')
            except Denied as error:
                out['excluded_target_check'] = str(error)
        print(json.dumps(out, indent=2))
    except Denied as error:
        parser.exit(2, f'DENIED: {error}\n')

if __name__ == '__main__':
    main()

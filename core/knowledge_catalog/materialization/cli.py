from __future__ import annotations
import argparse, json
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from .engine import RuntimeKnowledgeMaterializer
from .search import search_runtime_knowledge

def main() -> int:
    parser = argparse.ArgumentParser(description='JARVIS Genesis IX-A3 Runtime Knowledge Materialization')
    parser.add_argument('--database', type=Path, default=DEFAULT_CATALOG_DB)
    subs = parser.add_subparsers(dest='command', required=True)
    mat = subs.add_parser('materialize')
    mat.add_argument('--limit', type=int)
    mat.add_argument('--force', action='store_true')
    mat.add_argument('--chunk-chars', type=int, default=3200)
    mat.add_argument('--overlap-chars', type=int, default=320)
    sea = subs.add_parser('search')
    sea.add_argument('query')
    sea.add_argument('--limit', type=int, default=8)
    args = parser.parse_args()
    if args.command == 'materialize':
        service = RuntimeKnowledgeMaterializer(database_path=args.database,target_chunk_chars=args.chunk_chars,overlap_chars=args.overlap_chars)
        print(json.dumps(service.materialize(limit=args.limit, force=args.force).to_dict(), indent=2))
    else:
        print(json.dumps(search_runtime_knowledge(args.query, db_path=args.database, limit=args.limit), indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

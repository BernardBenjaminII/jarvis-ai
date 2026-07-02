import argparse
from pathlib import Path

from core.knowledge_mapper.report import print_summary
from core.knowledge_mapper.mapper import map_path

parser = argparse.ArgumentParser()

sub = parser.add_subparsers(dest="command")

m = sub.add_parser("map")
m.add_argument("path")

s = sub.add_parser("summary")
s.add_argument(
    "--root",
    default="/media/abdullah/JARVISDATA/Knowledge"
)

args = parser.parse_args()

if args.command == "map":

    print(map_path(args.path))

elif args.command == "summary":

    print_summary(Path(args.root))

import argparse

from core.knowledge_mapper.mapper import map_path

parser = argparse.ArgumentParser()

parser.add_argument("path")

args = parser.parse_args()

print(map_path(args.path))

import argparse
import json
from .identity import inventory
from .fixture import demo

parser = argparse.ArgumentParser(description='R2 identity inventory and local fixture only')
parser.add_argument('command', choices=('inventory', 'demo'))
args = parser.parse_args()
result = inventory() if args.command == 'inventory' else demo()
print(json.dumps(result, indent=2))
if args.command == 'demo' and not result['passed']:
    raise SystemExit(1)

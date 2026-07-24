from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[3]

BOOTSTRAP = ROOT / "core/bootstrap"

for file in sorted(BOOTSTRAP.glob("*.py")):

    tree = ast.parse(file.read_text())

    print()

    print(file.name)

    print("=" * 50)

    for node in tree.body:

        if isinstance(node, ast.If):

            try:
                text = ast.unparse(node.test)

            except Exception:
                continue

            if "__name__" in text:

                print("Contains executable entry point")

        if isinstance(node, ast.FunctionDef):

            if node.name == "main":

                print("Contains main()")

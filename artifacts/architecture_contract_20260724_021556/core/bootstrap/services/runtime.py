from __future__ import annotations

import os


def ensure_runtime(paths):
    print("Verifying runtime storage...")

    runtime = paths["runtime"]

    if not runtime.exists():
        print(f"Runtime path does not exist yet: {runtime}")
        print("Creating runtime directories...")

    directories = [
        paths["runtime"],
        paths["models"],
        paths["logs"],
        paths["vector_db"],
        paths["projects"],
        paths["venv"],
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    os.environ["OLLAMA_MODELS"] = str(paths["models"])

    print(f"Python  : {paths['python']}")
    print(f"Pip     : {paths['pip']}")
    print(f"Runtime : {paths['runtime']}")
    print(f"Models  : {paths['models']}")
    print(f"Venv    : {paths['venv']}")

    print("✓ Runtime storage available")

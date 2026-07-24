from __future__ import annotations

import subprocess
import sys

from core.src.cognition.model_registry import required_models


# ============================================================

# MODEL VERIFICATION

# ============================================================

def ensure_models():

    print("Checking models...")



    try:

        result = subprocess.run(

            ["ollama", "list"],

            capture_output=True,

            text=True,

            check=True,

        )



    except subprocess.CalledProcessError:

        print("✗ Could not read Ollama model list")

        sys.exit(1)



    installed = result.stdout.lower()



    missing = []



    for model in required_models():



        if model.lower() in installed:

            print(f"✓ {model} available")

        else:

            print(f"✗ {model} missing")

            missing.append(model)



    if missing:



        print()

        print("Missing models:")



        for model in missing:

            print(f"  - {model}")



        print()

        print("Install missing models with:")



        for model in missing:

            print(f"  ollama pull {model}")



        sys.exit(1)



    print("✓ All required models available")






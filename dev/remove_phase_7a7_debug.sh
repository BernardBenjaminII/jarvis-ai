#!/usr/bin/env bash
set -euo pipefail

FILE="dev/tests/acquisition/test_phase_7a7.py"

cp "${FILE}" "${FILE}.bak"

python3 <<'PY'
from pathlib import Path
import re

path = Path("dev/tests/acquisition/test_phase_7a7.py")
text = path.read_text()

#
# Remove expected/actual UUID debugging
#
patterns = [

r'''
\s*print\(\)
\s*expected\s*=\s*\{
.*?
\s*actual\s*=\s*set\(execution\.calls\)
.*?
\s*assert len\(execution\.calls\)
''',

r'''
\s*print\(\)
\s*expected\s*=\s*\{
.*?
\s*actual\s*=\s*set\(registration\.calls\)
.*?
\s*assert len\(registration\.calls\)
''',

r'''
\s*print\(\)
\s*print\("Configured failing object UUID:"\)
.*?
\s*print\("=+"\)
'''
]

for pattern in patterns:
    text = re.sub(
        pattern,
        "\n",
        text,
        flags=re.S | re.X,
    )

path.write_text(text)

print("[PASS] Debug prints removed.")
PY

echo
echo "Compiling..."

/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
-m py_compile "${FILE}"

echo
echo "[PASS] Compilation successful."
echo
echo "Run:"
echo
echo "/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \\"
echo "-m dev.tests.acquisition.test_phase_7a7"

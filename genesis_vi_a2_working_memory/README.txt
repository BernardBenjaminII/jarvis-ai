GENESIS VI-A2 — EXECUTIVE WORKING MEMORY

PREREQUISITE
------------
Genesis VI-A1 Step 1 must already be installed and certified.

INSTALLATION
------------
1. Extract the archive.

2. Enter the extracted directory:

   cd genesis_vi_a2_working_memory

3. Install into JARVIS:

   ./dev/install_genesis_vi_a2.sh \
     /media/abdullah/JARVISDATA/Projects/jarvis-ai

4. Enter the JARVIS project:

   cd /media/abdullah/JARVISDATA/Projects/jarvis-ai

5. Verify:

   PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
   ./dev/verify_genesis_vi_a2.sh

EXPECTED RESULT
---------------
Checks failed : 0
Overall status: EXCELLENT

RECOMMENDED BRANCH
------------------
feature/genesis-vi-a2-executive-working-memory

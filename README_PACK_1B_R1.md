# Genesis VII-C0 Pack 1B-R1

Complete revision correcting the Pack 1B self-verification defect.

## Install

```bash
unzip -o genesis_vii_c0_pack1b_r1.zip -d .
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/install_genesis_vii_c0_pack1b_r1.sh
```

## Verify again

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vii_c0_pack1b_r1.sh
```

The scripts set `PYTHONPATH` themselves. No manual `PYTHONPATH` prefix is required.

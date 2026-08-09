# Genesis IX-A4.3C — Executive Runtime Call Graph Reconstruction

Reconstructs the actual live Executive callable surface and orchestration flow without assuming `ExecutiveDirector.execute()` exists. It identifies whether the Director is truly in the execution path, resolves the actual callable when possible, and emits a repair contract for IX-A4.3B.

Outputs are written under `docs/audits/genesis_ix_a4_3c/`.

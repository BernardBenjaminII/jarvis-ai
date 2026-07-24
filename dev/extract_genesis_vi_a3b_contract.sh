#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="genesis_vi_a3b_contract"
mkdir -p "$OUTPUT_DIR"

echo "=========================================================="
echo "Extracting Genesis VI-A3B Compatibility Contract"
echo "=========================================================="

FILES=(
    "core/src/routes/operations.py"

    "core/integration/__init__.py"
    "core/integration/contracts.py"
    "core/integration/bootstrap.py"
    "core/integration/service.py"
    "core/integration/registry.py"

    "tests/test_genesis_ui_a2_executive_projection_framework.py"
    "tests/test_genesis_ui_a3_capability_discovery_registration.py"
    "tests/test_genesis_ui_a41_knowledge_inventory_projection.py"

    "tests/test_genesis_vi_a2_executive_mission_control.py"
    "tests/test_genesis_vi_a3_executive_projection_bus.py"

    "dev/verification/verify_genesis_ui_a2_executive_projection_framework.py"
    "dev/verification/verify_genesis_ui_a3_capability_discovery_registration.py"
    "dev/verification/verify_genesis_ui_a41_knowledge_inventory_projection.py"

    "dev/verification/verify_genesis_vi_a2_executive_mission_control.py"
    "dev/verification/verify_genesis_vi_a3_executive_projection_bus.py"
)

for file in "${FILES[@]}"
do
    if [[ -f "$file" ]]; then
        echo "[COPY] $file"
        mkdir -p "$OUTPUT_DIR/$(dirname "$file")"
        cp "$file" "$OUTPUT_DIR/$file"
    else
        echo "[MISSING] $file"
    fi
done

echo
echo "Generating route inventory..."

grep -R "@router.get" core/src/routes \
    > "$OUTPUT_DIR/route_inventory.txt" || true

grep -R "@router.post" core/src/routes \
    >> "$OUTPUT_DIR/route_inventory.txt" || true

grep -R "@app.get" core/src/routes \
    >> "$OUTPUT_DIR/route_inventory.txt" || true

grep -R "@app.post" core/src/routes \
    >> "$OUTPUT_DIR/route_inventory.txt" || true

echo
echo "Generating integration export inventory..."

grep -R "__all__" core/integration \
    > "$OUTPUT_DIR/public_exports.txt" || true

echo
echo "Generating projection inventory..."

grep -R "Projection" core/integration \
    > "$OUTPUT_DIR/projection_inventory.txt" || true

echo
echo "Generating bridge inventory..."

grep -R "bridge" core \
    > "$OUTPUT_DIR/bridge_inventory.txt" || true

echo
echo "Generating capability inventory..."

grep -R "capabilities" core \
    > "$OUTPUT_DIR/capability_inventory.txt" || true

echo
echo "Generating projections inventory..."

grep -R "projections" core \
    > "$OUTPUT_DIR/projections_inventory.txt" || true

echo
echo "Creating archive..."

tar -czf genesis_vi_a3b_contract.tar.gz \
    "$OUTPUT_DIR"

echo
echo "=========================================================="
echo "DONE"
echo
echo "Archive:"
echo
echo "genesis_vi_a3b_contract.tar.gz"
echo
echo "=========================================================="

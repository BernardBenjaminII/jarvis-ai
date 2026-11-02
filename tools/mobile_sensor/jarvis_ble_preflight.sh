#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

echo "============================================================"
echo " JARVIS BLE R1 PREFLIGHT"
echo "============================================================"
echo "Host:   $(hostname)"
echo "Python: $PYTHON"
echo

echo "=== BLUETOOTH SERVICE ==="
systemctl is-active bluetooth 2>/dev/null || true
echo

echo "=== CONTROLLER ==="
bluetoothctl show 2>/dev/null || true
echo

echo "=== RFKILL ==="
rfkill list bluetooth 2>/dev/null || true
echo

echo "=== BLUEZ ==="
bluetoothctl --version 2>/dev/null || true
echo

echo "=== PYTHON / BLEAK ==="
"$PYTHON" - <<'PY'
import sys
print("python:", sys.version.split()[0])
try:
    import bleak
    try:
        from importlib.metadata import version
        print("bleak:", version("bleak"))
    except Exception:
        print("bleak: imported")
except Exception as e:
    print("bleak: MISSING:", e)
PY
echo

echo "=== JARVIS MOBILE API ==="
curl -fsS http://127.0.0.1:8000/api/sensors/mobile/status || true
echo
echo

echo "If Bluetooth is powered and bleak is installed, open the"
echo "JarvisSensorNode app on the iPhone and run:"
echo
echo "  $PYTHON tools/mobile_sensor/ble_bridge.py --verbose"

#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$ROOT/systemd"

if [[ $# -ne 1 ]]; then
    echo "Usage:"
    echo "  sudo $0 <IPHONE_UDID>"
    exit 2
fi

IPHONE_UDID="$1"

if [[ ! "$IPHONE_UDID" =~ ^[A-Za-z0-9-]+$ ]]; then
    echo "Invalid iPhone UDID."
    exit 2
fi

if [[ ! -x /usr/bin/iproxy ]]; then
    echo "Missing /usr/bin/iproxy"
    exit 1
fi

install -d -m 755 /etc/jarvis

if [[ ! -f /etc/jarvis/mobile-sensor.env ]]; then
    install \
        -m 600 \
        "$SYSTEMD_DIR/mobile-sensor.env.example" \
        /etc/jarvis/mobile-sensor.env

    echo
    echo "Created /etc/jarvis/mobile-sensor.env"
    echo "Set JARVIS_MOBILE_SENSOR_TOKEN before starting the bridge."
    echo
fi

sed \
    "s/__IPHONE_UDID__/${IPHONE_UDID}/g" \
    "$SYSTEMD_DIR/jarvis-mobile-usb-tunnel.service.in" \
    > /etc/systemd/system/jarvis-mobile-usb-tunnel.service

install \
    -m 644 \
    "$SYSTEMD_DIR/jarvis-mobile-bridge.service" \
    /etc/systemd/system/jarvis-mobile-bridge.service

systemctl daemon-reload

echo
echo "Installed:"
echo "  jarvis-mobile-usb-tunnel.service"
echo "  jarvis-mobile-bridge.service"
echo
echo "iPhone:"
echo "  $IPHONE_UDID"
echo
echo "After configuring /etc/jarvis/mobile-sensor.env:"
echo
echo "  systemctl enable --now \\"
echo "    jarvis-mobile-usb-tunnel.service \\"
echo "    jarvis-mobile-bridge.service"

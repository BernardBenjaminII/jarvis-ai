#!/bin/bash

set -e

cd "$(dirname "$0")"

echo
echo "🧠 Starting JARVIS..."
echo

exec python3 launcher.py

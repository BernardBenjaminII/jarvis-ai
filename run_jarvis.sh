#!/bin/bash

set -e

echo "🧠 Starting JARVIS system..."

# ============================================================

# CONFIGURATION

# ============================================================

OLLAMA_HOST="http://127.0.0.1:11434"

JARVIS_RUNTIME="/mnt/jarvis_runtime"

OLLAMA_MODELS="$JARVIS_RUNTIME/ollama/models"
LOG_DIR="$JARVIS_RUNTIME/logs"
VECTOR_DB_DIR="$JARVIS_RUNTIME/vector_db"
VENV_DIR="$JARVIS_RUNTIME/venvs/jarvis"

MODELS=(
"mistral"
)

export OLLAMA_MODELS

# ============================================================

# PRE-FLIGHT CHECKS

# ============================================================

echo "🔍 Verifying runtime storage..."

if ! mountpoint -q "$JARVIS_RUNTIME"; then
echo "❌ JARVIS runtime drive is not mounted:"
echo "   $JARVIS_RUNTIME"
exit 1
fi

mkdir -p "$OLLAMA_MODELS"
mkdir -p "$LOG_DIR"
mkdir -p "$VECTOR_DB_DIR"
mkdir -p "$JARVIS_RUNTIME/venvs"

echo "✅ Runtime storage available"

# ============================================================

# VERIFY OLLAMA INSTALLED

# ============================================================

if ! command -v ollama >/dev/null 2>&1; then
echo "❌ Ollama is not installed"
exit 1
fi

# ============================================================

# OLLAMA HEALTH CHECK

# ============================================================

check_ollama() {
curl -s "$OLLAMA_HOST/api/tags" >/dev/null 2>&1
}

echo "🔍 Checking Ollama..."

if check_ollama; then
echo "✅ Ollama already running"
else
echo "🚀 Starting Ollama..."


nohup ollama serve \
    > "$LOG_DIR/ollama.log" \
    2>&1 &

sleep 5

fi

if ! check_ollama; then
echo "❌ Ollama failed to start"
echo "📄 Check:"
echo "   $LOG_DIR/ollama.log"
exit 1
fi

echo "✅ Ollama online"

# ============================================================

# VERIFY REQUIRED MODELS

# ============================================================

echo "🧠 Checking models..."

for MODEL in "${MODELS[@]}"; do
if ollama list | grep -q "^$MODEL"; then
echo "✅ $MODEL available"
else
echo "⬇️ Pulling model: $MODEL"
ollama pull "$MODEL"
fi
done

# ============================================================

# PYTHON ENVIRONMENT

# ============================================================

echo "🐍 Preparing Python environment..."

if [ ! -x "$VENV_DIR/bin/python" ]; then
echo "📦 Creating virtual environment..."
python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Using Python: $(which python)"
echo "Using Pip: $(which pip)"

# ============================================================

# DEPENDENCIES (ONE-TIME INSTALL)

# ============================================================

if [ ! -f "$VENV_DIR/.deps_installed" ]; then

echo "📦 Installing dependencies..."

python -m pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install \
        fastapi \
        uvicorn \
        python-multipart \
        PyMuPDF
fi

touch "$VENV_DIR/.deps_installed"

else
echo "✅ Dependencies already installed"
fi

# ============================================================

# JARVIS API

# ============================================================

echo "🚀 Launching JARVIS API..."

export PYTHONPATH="$PWD/core"

uvicorn core.src.main:app --host 0.0.0.0 --port 5001

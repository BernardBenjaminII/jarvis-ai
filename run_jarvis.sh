#!/bin/bash

echo "🧠 Starting JARVIS system..."

# ---- CONFIG ----
OLLAMA_HOST="http://127.0.0.1:11434"
MODELS=("mistral")   # add more later: "tinyllama" "phi3"

# ---- FUNCTION: check if ollama is running ----
check_ollama() {
    curl -s http://127.0.0.1:11434/api/tags > /dev/null
    return $?
}
# ---- START OLLAMA IF NOT RUNNING ----
echo "🔍 Checking Ollama..."

if check_ollama; then
    echo "✅ Ollama already running"
else
    echo "🚀 Starting Ollama..."
    nohup ollama serve > logs/ollama.log 2>&1 &
    sleep 3
fi

# ---- VERIFY OLLAMA STARTED ----
if ! check_ollama; then
    echo "❌ Ollama failed to start"
    exit 1
fi

echo "🧠 Ollama is online"

# ---- ENSURE MODELS EXIST ----
for MODEL in "${MODELS[@]}"; do
    if ! ollama list | grep -q "$MODEL"; then
        echo "⬇️ Pulling model: $MODEL"
        ollama pull $MODEL
    else
        echo "✅ Model $MODEL already available"
    fi
done
# ---- SETUP PYTHON ENV ----
echo "🐍 Setting up Python environment..."

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# ---- INSTALL DEPENDENCIES ----
echo "📦 Installing dependencies..."

pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ No requirements.txt found, installing core dependencies..."
    pip install fastapi uvicorn python-multipart PyMuPDF
fi
# ---- START JARVIS ----
echo "🚀 Launching JARVIS API..."
# ---- FIX PYTHON PATH ----
export PYTHONPATH=$PWD/core
uvicorn core.src.main:app --host 0.0.0.0 --port 5001

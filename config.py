import os

JARVIS_ROOT = os.getenv(
    "JARVIS_ROOT",
    r"E:\JARVIS_HOME"
)

MEMORY_PATH = os.path.join(JARVIS_ROOT, "memory")
MODELS_PATH = os.path.join(JARVIS_ROOT, "models")
KNOWLEDGE_PATH = os.path.join(JARVIS_ROOT, "knowledge")
LOG_PATH = os.path.join(JARVIS_ROOT, "logs", "jarvis.log")
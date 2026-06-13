import requests
import os
from openai import OpenAI


# 🔍 Check if Ollama is running
def is_ollama_available():
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except:
        return False


# 🧠 Local LLM (Ollama)
def query_local(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
	    "options": {
		"num_predict": 120, 
		"temperature": 0.2
	    }
        },
        timeout=60
    )

    data = response.json()
    print("[DEBUG] Ollama raw response:", data)  # 👈 keep this for now

    # ✅ Normal case
    if "response" in data:
        return data["response"], "mistral/local"

    # ⚠️ Chat-style fallback
    if "message" in data and "content" in data["message"]:
        return data["message"]["content"], "mistral/local"

    # ❌ Error case
    if "error" in data:
        raise Exception(data["error"])

    raise Exception(f"Unknown Ollama response format: {data}")

# ☁️ Cloud LLM (OpenAI)
def query_cloud(prompt):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content, "openai/cloud"


# 🚀 MAIN ENTRY
def query_llm(prompt: str, model: str = "mistral") -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        if response.status_code != 200:
            return f"[LLM ERROR] Local model returned status {response.status_code}"

        data = response.json()

        # Safe parse
        raw = ""
        if "response" in data:
            raw = data["response"]
        elif "message" in data and "content" in data["message"]:
            raw = data["message"]["content"]
        else:
            return f"[LLM ERROR] Unknown response format: {data}"

        raw = raw.strip()

        # HARD FILTER
        kill_blocks = [
            "SYSTEM:",
            "MODE:",
            "OUTPUT FORMAT",
            "CONSTRAINTS",
            "DATA:",
            "QUERY:",
        ]

        for block in kill_blocks:
            if block in raw:
                raw = raw.split(block)[0]

        junk_phrases = [
            "JARVIS:",
            "(pleasant and authoritative)",
            "(preparing for user query)",
            "Question:",
        ]

        for phrase in junk_phrases:
            raw = raw.replace(phrase, "")

        # Clean lines
        lines = []
        for line in raw.splitlines():
            line = line.strip()
            if line:
                lines.append(line)

        raw = "\n".join(lines)

        # Final trim
        raw = raw[:600]

        return raw

    except Exception as e:
        return f"[LLM ERROR] Local model failed: {str(e)}"

import os
import requests
from openai import OpenAI

# ============================================================
# OLLAMA HEALTH CHECK
# ============================================================

def is_ollama_available():
    try:
        response = requests.get(
            "http://127.0.0.1:11434/api/tags",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


# ============================================================
# LOCAL LLM (OLLAMA)
# ============================================================

def query_local(prompt: str):

    payload = {
        "model": "mistral:latest",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 120
        }
    }

    print(f"[DEBUG] Sending to Ollama: {payload}")

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json=payload,
        timeout=120
    )

    print(f"[DEBUG] Ollama status: {response.status_code}")
    print(f"[DEBUG] Ollama raw response: {response.text}")

    if response.status_code != 200:
        raise Exception(
            f"Ollama returned {response.status_code}: {response.text}"
        )

    data = response.json()

    if "response" in data:
        return data["response"], "mistral/local"

    if "message" in data and "content" in data["message"]:
        return data["message"]["content"], "mistral/local"

    if "error" in data:
        raise Exception(data["error"])

    raise Exception(
        f"Unknown Ollama response format: {data}"
    )


# ============================================================
# CLOUD LLM (OPENAI)
# ============================================================

def query_cloud(prompt: str):

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content, "openai/cloud"


# ============================================================
# MAIN ROUTER
# ============================================================

def query_llm(
    prompt: str,
    model: str = "mistral:latest"
) -> str:

    try:

        print(f"[DEBUG] MODEL={model}")
        print(f"[DEBUG] PROMPT={prompt}")

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        print(f"[DEBUG] PAYLOAD={payload}")

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json=payload,
            timeout=120
        )

        print(f"[DEBUG] STATUS={response.status_code}")
        print(f"[DEBUG] RESPONSE={response.text}")

        if response.status_code != 200:
            return (
                f"[LLM ERROR] Status {response.status_code}\n"
                f"Response: {response.text}"
            )

        data = response.json()

        if "response" in data:
            raw = data["response"]

        elif (
            "message" in data
            and "content" in data["message"]
        ):
            raw = data["message"]["content"]

        else:
            return (
                f"[LLM ERROR] Unknown response format:\n{data}"
            )

        raw = raw.strip()

        kill_blocks = [
            "SYSTEM:",
            "MODE:",
            "OUTPUT FORMAT",
            "CONSTRAINTS",
            "DATA:",
            "QUERY:"
        ]

        for block in kill_blocks:
            if block in raw:
                raw = raw.split(block)[0]

        junk_phrases = [
            "JARVIS:",
            "(pleasant and authoritative)",
            "(preparing for user query)",
            "Question:"
        ]

        for phrase in junk_phrases:
            raw = raw.replace(phrase, "")

        lines = []

        for line in raw.splitlines():
            line = line.strip()

            if line:
                lines.append(line)

        raw = "\n".join(lines)

        return raw[:600]

    except Exception as e:

        return (
            f"[LLM ERROR] Local model failed:\n"
            f"{str(e)}"
        )

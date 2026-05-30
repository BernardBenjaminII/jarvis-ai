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


# 🧼 Clean model output (prevents duplicate tags)
def clean_response(text):
    if text.startswith("[JARVIS"):
        return text.split("]", 1)[-1].strip()
    return text.strip()


# 🧠 Local LLM with fallback models
def query_local(prompt):

    models = ["tinyllama", "phi3", "mistral"]  # ⚡ ordered by speed → power

    for model in models:
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=180  # ⬅️ increased timeout
            )

            data = response.json()
            print(f"[DEBUG] ({model}) response:", data)

            if "response" in data:
                return clean_response(data["response"]), f"{model}/local"

            if "message" in data and "content" in data["message"]:
                return clean_response(data["message"]["content"]), f"{model}/local"

            if "error" in data:
                raise Exception(data["error"])

        except Exception as e:
            print(f"[LLM] {model} failed: {e}")
            continue

    raise Exception("All local models failed")


# ☁️ Cloud LLM (OpenAI)
def query_cloud(prompt):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return clean_response(response.choices[0].message.content), "openai/cloud"


# 🚀 MAIN ENTRY
def query_llm(prompt, mode="auto"):

    if mode == "auto":
        if is_ollama_available():
            try:
                response, tag = query_local(prompt)
                return f"[JARVIS: {tag}]\n{response}"
            except Exception as e:
                print(f"[LLM] Local failed: {e}")

        try:
            response, tag = query_cloud(prompt)
            return f"[JARVIS: {tag}]\n{response}"
        except Exception as e:
            return f"[LLM ERROR] Cloud failed: {str(e)}"

    if mode == "local":
        try:
            response, tag = query_local(prompt)
            return f"[JARVIS: {tag}]\n{response}"
        except Exception as e:
            return f"[LLM ERROR] Local failed: {str(e)}"

    if mode == "cloud":
        try:
            response, tag = query_cloud(prompt)
            return f"[JARVIS: {tag}]\n{response}"
        except Exception as e:
            return f"[LLM ERROR] Cloud failed: {str(e)}"

    return "[LLM ERROR] Invalid mode"

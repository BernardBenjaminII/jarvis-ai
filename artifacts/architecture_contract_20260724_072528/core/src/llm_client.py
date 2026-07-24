import os
import requests
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_llm(prompt: str, model: str = "mistral") -> str:
    try:
        # ☁️ CLOUD
        if model == "cloud":
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return r.choices[0].message.content

        # 🧠 LOCAL (Ollama)
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        r.raise_for_status()
        return r.json()["response"]

    except Exception as e:
        return f"[LLM ERROR] {e}"

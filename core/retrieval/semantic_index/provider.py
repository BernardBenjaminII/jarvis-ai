from __future__ import annotations
import json, urllib.request

class OllamaEmbeddingProvider:
    def __init__(self, *, base_url: str="http://127.0.0.1:11434", model: str="mxbai-embed-large", timeout: int=120):
        self.base_url=base_url.rstrip("/")
        self.model=model
        self.timeout=timeout

    def health(self):
        try:
            with urllib.request.urlopen(self.base_url + "/api/tags", timeout=5) as r:
                data=json.loads(r.read().decode("utf-8"))
            models=[str(x.get("name","")) for x in data.get("models",[])]
            return {"available":True,"models":models,"model_present":any(x.split(":")[0]==self.model.split(":")[0] for x in models)}
        except Exception as exc:
            return {"available":False,"models":[],"model_present":False,"error":f"{type(exc).__name__}: {exc}"}

    def embed_batch(self, texts):
        payload=json.dumps({"model":self.model,"input":list(texts)}).encode("utf-8")
        req=urllib.request.Request(
            self.base_url + "/api/embed",
            data=payload,
            headers={"Content-Type":"application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data=json.loads(r.read().decode("utf-8"))
        embeddings=data.get("embeddings")
        if not isinstance(embeddings,list) or len(embeddings)!=len(texts):
            raise RuntimeError("Ollama returned an unexpected embeddings payload.")
        return embeddings

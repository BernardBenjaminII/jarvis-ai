from __future__ import annotations
import json, urllib.request
import urllib.error

class EmbeddingProviderHTTPError(RuntimeError):
    def __init__(self, message, *, status=None, body=""):
        super().__init__(message)
        self.status = status
        self.body = body


class EmbeddingContextLengthError(EmbeddingProviderHTTPError):
    pass


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
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data=json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                raw=exc.read()
                body=raw.decode("utf-8","replace") if isinstance(raw,(bytes,bytearray)) else str(raw)
            except Exception:
                body=""
            status=getattr(exc,"code",None)
            low=body.lower()
            message=f"HTTP {status}: {body or getattr(exc,'reason','HTTP error')}"
            if status==400 and (
                "input length exceeds the context length" in low
                or ("context length" in low and "exceed" in low)
            ):
                raise EmbeddingContextLengthError(message,status=status,body=body) from exc
            raise EmbeddingProviderHTTPError(message,status=status,body=body) from exc
        embeddings=data.get("embeddings")
        if not isinstance(embeddings,list) or len(embeddings)!=len(texts):
            raise RuntimeError("Ollama returned an unexpected embeddings payload.")
        return embeddings

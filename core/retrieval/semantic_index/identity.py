from __future__ import annotations
import uuid

NAMESPACE = uuid.UUID("b728b9a0-711c-4d2b-b99f-bdd39a4d00c1")

def stable_chunk_uuid(*, document_id: int, chunk_id: int, content_sha256: str) -> str:
    material = f"runtime:{document_id}:{chunk_id}:{content_sha256}"
    return str(uuid.uuid5(NAMESPACE, material))

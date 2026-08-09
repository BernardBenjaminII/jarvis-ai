import hashlib, json
from pathlib import Path

def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True) + "\n")

def archive_results(run_root, results):
    values = tuple(results)
    write_jsonl(run_root/"results.jsonl", (x.to_dict() for x in values))
    write_jsonl(run_root/"failures.jsonl", (x.to_dict() for x in values if not x.passed))
    hashes = {
        str(p.relative_to(run_root)): sha256_file(p)
        for p in sorted(run_root.rglob("*")) if p.is_file()
    }
    return {"artifact_hashes": hashes}

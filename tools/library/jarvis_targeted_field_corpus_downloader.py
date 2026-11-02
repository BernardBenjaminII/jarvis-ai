#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import re
import shutil
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LIBRARY = Path("/srv/storage2/Library")
ROOT = LIBRARY / "16_Survival_Resilience"
ACQ = ROOT / "_Acquisition"
MANIFEST = ACQ / "field_corpus_manifest.json"

LOG = ACQ / "acquisition_log.jsonl"
HAVE = ACQ / "already_present.jsonl"
REJECTED = ACQ / "rejected.jsonl"
REPORT = ACQ / "acquisition_report.txt"
HASHFILE = ACQ / "hashes.sha256"
GLOBAL_HASH_CACHE = ACQ / "global_pdf_hashes.json"

UA = "Mozilla/5.0 (X11; Linux x86_64) Jarvis-Corpus-Downloader/3.0"

BLOCKED = {
    "classified", "top secret", "secret//", "noforn", "fedcon",
    "for official use only", "fouo", "controlled unclassified",
    "restricted distribution"
}

SEARCH_ROOTS = [
    LIBRARY / "14_Military_Defense",
    LIBRARY / "15_Intelligence_Security",
    LIBRARY / "16_Survival_Resilience",
    LIBRARY / "27_Practical_Skills",
    LIBRARY / "30_Transportation",
    LIBRARY / "42_Technical_Documentation",
]



def corpus_release():
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return str(data.get("release") or "UNVERSIONED")
    except Exception:
        return "UNVERSIONED"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def norm(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def policy_check(doc):
    if doc.get("access") != "public":
        return False, "not explicitly public"

    blob = json.dumps(doc, ensure_ascii=False).lower()

    for marker in BLOCKED:
        if marker in blob:
            return False, f"restricted marker: {marker}"

    return True, "approved"


def allowed_url(doc, url):
    try:
        host = urllib.parse.urlparse(url).hostname or ""
    except Exception:
        return False

    host = host.lower()

    allowed = [x.lower() for x in doc.get("allowed_domains", [])]

    if not allowed:
        return False

    return any(host == d or host.endswith("." + d) for d in allowed)


class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        attrs = dict(attrs)
        href = attrs.get("href")

        if href:
            self.links.append(href)


def fetch_html(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8"},
    )

    ctx = ssl.create_default_context()

    with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
        ctype = (r.headers.get("Content-Type") or "").lower()
        data = r.read(8 * 1024 * 1024)

    if "html" not in ctype and b"<html" not in data[:4096].lower():
        return None

    return data.decode("utf-8", errors="replace")


def discover_pdf_links(doc):
    landing = doc.get("landing_url")

    if not landing or not allowed_url(doc, landing):
        return []

    try:
        text = fetch_html(landing)
    except Exception:
        return []

    if not text:
        return []

    parser = LinkParser()

    try:
        parser.feed(text)
    except Exception:
        return []

    links = []

    for href in parser.links:
        absolute = urllib.parse.urljoin(landing, href)

        if not allowed_url(doc, absolute):
            continue

        low = absolute.lower()

        if ".pdf" in low or "/download" in low or "/sites/default/files/" in low:
            links.append(absolute)

    return list(dict.fromkeys(links))


def score_candidate(doc, url):
    u = norm(urllib.parse.unquote(url))
    score = 0

    language = doc.get("language", "")

    terms = []

    if doc.get("publication"):
        terms.append(norm(doc["publication"]))

    for kw in doc.get("keywords", []):
        n = norm(kw)
        if len(n) >= 4:
            terms.append(n)

    for term in terms:
        if term and term in u:
            score += 5

    if language == "en" and any(x in u for x in ("english", "enpdf", "_en", "-en")):
        score += 3
    elif language == "ar" and any(x in u for x in ("arabic", "_ar", "-ar")):
        score += 3
    elif language == "fr" and any(x in u for x in ("french", "_fr", "-fr")):
        score += 3
    elif language == "es" and any(x in u for x in ("spanish", "_es", "-es")):
        score += 3

    if ".pdf" in url.lower():
        score += 2

    return score


def probe_candidate(doc, url):
    """Verify that a discovered candidate actually resolves on an allowed domain."""
    try:
        url = iri_to_uri(url)

        if not allowed_url(doc, url):
            return False

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "application/pdf,*/*;q=0.5",
                "Range": "bytes=0-7",
            },
        )

        ctx = ssl.create_default_context()

        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            final_url = r.geturl()

            if not allowed_url(doc, final_url):
                return False

            header = r.read(8)

            return header.startswith(b"%PDF-")

    except Exception:
        return False


def resolve_url(doc):
    direct = doc.get("download_url")

    if direct:
        if allowed_url(doc, direct):
            return direct, "manifest"
        return None, "direct URL failed domain policy"

    candidates = discover_pdf_links(doc)

    if not candidates:
        return None, "no authoritative PDF candidate discovered"

    ranked = sorted(
        ((score_candidate(doc, u), u) for u in candidates),
        reverse=True
    )

    # A page can retain links to files that no longer exist.
    # Reject dead/non-PDF candidates before selecting a winner.
    ranked = [
        (score, url)
        for score, url in ranked
        if probe_candidate(doc, url)
    ]

    if not ranked:
        return None, "PDF candidates discovered but none validated as live PDFs"

    best_score, best_url = ranked[0]

    # Do not guess among weak/ambiguous links.
    if best_score < 2:
        return None, "PDF links found but none confidently matched"

    if len(ranked) > 1 and ranked[1][0] == best_score:
        return None, "multiple equally-ranked PDF candidates"

    return best_url, "authoritative landing-page discovery"


def language_from_filename(path):
    """
    Infer language only when a filename carries a reasonably explicit
    language marker. Return None when the filename gives us no reliable
    language evidence.

    IMPORTANT:
    Unknown language is not treated as proof of compatibility for
    multilingual manifest records.
    """
    name = str(Path(path).name).lower()

    patterns = {
        "en": (
            r"(?:^|[_\-. ])en(?:[_\-. ]|$)",
            r"(?:^|[_\-. ])eng(?:lish)?(?:[_\-. ]|$)",
            r"english",
        ),
        "fr": (
            r"(?:^|[_\-. ])fr(?:[_\-. ]|$)",
            r"(?:^|[_\-. ])fra(?:[_\-. ]|$)",
            r"french",
            r"francais",
            r"français",
        ),
        "es": (
            r"(?:^|[_\-. ])es(?:[_\-. ]|$)",
            r"(?:^|[_\-. ])spa(?:nish)?(?:[_\-. ]|$)",
            r"spanish",
            r"espanol",
            r"español",
        ),
        "ar": (
            r"(?:^|[_\-. ])ar(?:[_\-. ]|$)",
            r"(?:^|[_\-. ])ara(?:bic)?(?:[_\-. ]|$)",
            r"arabic",
        ),
    }

    for lang, pats in patterns.items():
        for pat in pats:
            if re.search(pat, name, re.I):
                return lang

    return None


def sidecar_language(path):
    """
    Prefer provenance metadata when available.
    """
    path = Path(path)
    sidecar = path.with_suffix(path.suffix + ".metadata.json")

    if not sidecar.exists():
        return None

    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception:
        return None

    lang = str(data.get("language") or "").strip().lower()

    return lang or None


def candidate_language(path):
    """
    Provenance is authoritative; filename inference is fallback.
    """
    return sidecar_language(path) or language_from_filename(path)


def language_compatible(doc, path):
    """
    A known language conflict is always a rejection.

    For explicitly multilingual manifest records (en/fr/es/ar), an
    unknown candidate language is also insufficient evidence for an
    automatic HAVE_EXISTING match. Such documents should be resolved
    normally or reviewed instead of guessed.
    """
    wanted = str(doc.get("language") or "").strip().lower()

    if not wanted:
        return True

    found = candidate_language(path)

    if found:
        return found == wanted

    # Do not allow an unidentified document to satisfy one member of a
    # multilingual set merely because its title/publication is similar.
    if wanted in {"en", "fr", "es", "ar"}:
        return False

    return True


def find_existing(doc):
    publication = norm(doc.get("publication", ""))
    title = norm(doc.get("title", ""))
    filename = norm(doc.get("filename", ""))

    keywords = [
        norm(x) for x in doc.get("keywords", [])
        if len(norm(x)) >= 6
    ]

    hits = []

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue

        for dp, _, files in os.walk(root):
            for name in files:
                if not name.lower().endswith(
                    (".pdf", ".epub", ".txt", ".html", ".htm")
                ):
                    continue

                candidate = Path(dp) / name
                n = norm(name)

                # Publication metadata is useful corroboration, but a
                # bare year such as "2025" or "2015" must NEVER identify
                # a document by itself. Otherwise every unrelated document
                # from the same year becomes a false HAVE_EXISTING match.
                publication_is_year = bool(
                    re.fullmatch(r"(?:19|20)\\d{2}", publication)
                )

                publication_identity = (
                    publication
                    and not publication_is_year
                    and len(publication) >= 8
                    and publication in n
                )

                filename_identity = (
                    filename
                    and len(filename) >= 12
                    and filename in n
                )

                title_identity = (
                    len(title) >= 12
                    and title in n
                )

                kh = sum(1 for k in keywords if k in n)

                strong = (
                    publication_identity
                    or filename_identity
                    or title_identity
                )

                if not (strong or kh >= 2):
                    continue

                if not language_compatible(doc, candidate):
                    continue

                hits.append(candidate)

    return sorted(set(hits))


def build_global_hash_index(force=False):
    if GLOBAL_HASH_CACHE.exists() and not force:
        try:
            return json.loads(GLOBAL_HASH_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass

    index = {}

    print("Building relevant-library PDF hash index...")

    count = 0

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() != ".pdf":
                continue

            try:
                digest = sha256(path)
            except OSError:
                continue

            index.setdefault(digest, []).append(str(path))
            count += 1

            if count % 250 == 0:
                print(f"  hashed {count:,} PDFs")

    GLOBAL_HASH_CACHE.write_text(
        json.dumps(index, indent=2, sort_keys=True),
        encoding="utf-8"
    )

    print(f"Hash index ready: {count:,} PDFs")
    return index


def iri_to_uri(url):
    """
    Convert Unicode/IRI URLs into ASCII-safe HTTP URLs while preserving
    URL structure and existing percent escapes.
    """
    parts = urllib.parse.urlsplit(url)

    path = urllib.parse.quote(
        urllib.parse.unquote(parts.path),
        safe="/:@!$&'()*+,;=-._~"
    )

    query = urllib.parse.quote(
        urllib.parse.unquote(parts.query),
        safe="=&?/:;+,%@-._~"
    )

    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, path, query, parts.fragment)
    )


def download_pdf(doc, url, temp):
    url = iri_to_uri(url)

    if not allowed_url(doc, url):
        raise RuntimeError("download URL violates domain allowlist")

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/pdf,*/*;q=0.5",
        },
    )

    ctx = ssl.create_default_context()

    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        final_url = r.geturl()

        if not allowed_url(doc, final_url):
            raise RuntimeError(
                f"redirect escaped authoritative domain: {final_url}"
            )

        ctype = (r.headers.get("Content-Type") or "").lower()

        with open(temp, "wb") as f:
            shutil.copyfileobj(r, f)

    size = temp.stat().st_size

    if size < 1024:
        raise RuntimeError(f"payload too small: {size} bytes")

    with open(temp, "rb") as f:
        header = f.read(8)

    if not header.startswith(b"%PDF-"):
        raise RuntimeError(
            f"payload is not a PDF; Content-Type={ctype}"
        )

    return final_url, ctype, size


def provenance(doc, source_url, destination, digest, size, method):
    sidecar = destination.with_suffix(destination.suffix + ".metadata.json")

    record = {
        "schema": 2,
        "release": corpus_release(),
        "acquired_at": utc(),
        "id": doc["id"],
        "title": doc["title"],
        "publisher": doc.get("publisher"),
        "publication": doc.get("publication"),
        "language": doc.get("language"),
        "document_status": doc.get("status"),
        "access": doc.get("access"),
        "track": doc.get("track"),
        "landing_url": doc.get("landing_url"),
        "source_url": source_url,
        "resolution_method": method,
        "sha256": digest,
        "bytes": size,
        "local_path": str(destination),
    }

    sidecar.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )


def write_report(rows):
    counts = {}

    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    out = [
        "=" * 78,
        f"JARVIS TARGETED FIELD CORPUS — {corpus_release()}",
        "=" * 78,
        f"Generated : {utc()}",
        f"Library   : {LIBRARY}",
        f"Manifest  : {MANIFEST}",
        "",
        "SUMMARY",
        "-" * 78,
    ]

    for k in sorted(counts):
        out.append(f"{k:28s} {counts[k]:5d}")

    out += ["", "DOCUMENTS", "-" * 78]

    for r in rows:
        out.append(f"[{r['status']}] {r['id']} — {r['title']}")

        for p in r.get("existing", []):
            out.append(f"    HAVE: {p}")

        if r.get("url"):
            out.append(f"    URL : {r['url']}")

        if r.get("destination"):
            out.append(f"    DEST: {r['destination']}")

        if r.get("reason"):
            out.append(f"    NOTE: {r['reason']}")

    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--mode",
        choices=("audit", "acquire"),
        default="audit"
    )
    ap.add_argument("--track", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rebuild-hashes", action="store_true")

    args = ap.parse_args()

    docs = load_manifest()["documents"]

    if args.track:
        wanted = set(args.track)
        docs = [d for d in docs if d.get("track") in wanted]

    rows = []

    hash_index = None

    if args.mode == "acquire":
        hash_index = build_global_hash_index(args.rebuild_hashes)

    print("=" * 78)
    print(f"JARVIS TARGETED FIELD CORPUS — {corpus_release()}")
    print("=" * 78)
    print(f"Mode: {args.mode}")
    print()

    for doc in docs:
        print(f"--- {doc['id']}: {doc['title']}")

        ok, reason = policy_check(doc)

        if not ok:
            row = {
                "id": doc["id"],
                "title": doc["title"],
                "status": "REJECTED",
                "reason": reason,
            }
            rows.append(row)
            append_jsonl(REJECTED, {"timestamp": utc(), **row})
            print(f"    REJECTED: {reason}")
            continue

        # Exact requested destination always takes precedence over
        # heuristic corpus-wide matching.
        destination = ROOT / doc["destination"] / doc["filename"]

        if destination.exists():
            row = {
                "id": doc["id"],
                "title": doc["title"],
                "status": "HAVE_DESTINATION",
                "existing": [str(destination)],
            }
            rows.append(row)
            print(f"    HAVE_DESTINATION: {destination}")
            continue

        existing = find_existing(doc)

        if existing:
            row = {
                "id": doc["id"],
                "title": doc["title"],
                "status": "HAVE_EXISTING",
                "existing": [str(x) for x in existing],
            }
            rows.append(row)

            print(f"    HAVE_EXISTING ({len(existing)})")
            for existing_path in existing[:8]:
                print(f"      {existing_path}")
            continue

        url, method = resolve_url(doc)

        if not url:
            row = {
                "id": doc["id"],
                "title": doc["title"],
                "status": "REVIEW",
                "reason": method,
                "destination": str(destination),
            }
            rows.append(row)
            print(f"    REVIEW: {method}")
            continue

        print(f"    RESOLVED: {url}")
        print(f"    METHOD  : {method}")

        if args.mode != "acquire" or args.dry_run:
            rows.append({
                "id": doc["id"],
                "title": doc["title"],
                "status": "READY",
                "url": url,
                "destination": str(destination),
                "reason": method,
            })
            print("    READY")
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)

        fd, tmpname = tempfile.mkstemp(
            prefix=".jarvis-r2a-",
            suffix=".pdf",
            dir=str(ACQ / "tmp")
        )
        os.close(fd)
        temp = Path(tmpname)

        try:
            final_url, ctype, size = download_pdf(doc, url, temp)
            digest = sha256(temp)

            duplicate_paths = (hash_index or {}).get(digest, [])

            if duplicate_paths:
                temp.unlink(missing_ok=True)

                row = {
                    "id": doc["id"],
                    "title": doc["title"],
                    "status": "DUPLICATE_HASH",
                    "existing": duplicate_paths,
                    "url": final_url,
                }
                rows.append(row)

                print("    DUPLICATE_HASH")
                for p in duplicate_paths[:5]:
                    print(f"      {p}")
                continue

            if destination.exists():
                raise RuntimeError("destination appeared during acquisition")

            temp.replace(destination)

            provenance(
                doc,
                final_url,
                destination,
                digest,
                size,
                method
            )

            with open(HASHFILE, "a", encoding="utf-8") as f:
                f.write(f"{digest}  {destination}\n")

            (hash_index or {}).setdefault(
                digest, []
            ).append(str(destination))

            record = {
                "timestamp": utc(),
                "release": corpus_release(),
                "id": doc["id"],
                "title": doc["title"],
                "source_url": final_url,
                "destination": str(destination),
                "sha256": digest,
                "bytes": size,
                "content_type": ctype,
                "resolution_method": method,
            }

            append_jsonl(LOG, record)

            rows.append({
                "id": doc["id"],
                "title": doc["title"],
                "status": "ACQUIRED",
                "url": final_url,
                "destination": str(destination),
            })

            print(f"    ACQUIRED: {destination}")
            print(f"    BYTES   : {size:,}")
            print(f"    SHA256  : {digest}")

            time.sleep(1)

        except Exception as exc:
            temp.unlink(missing_ok=True)

            row = {
                "id": doc["id"],
                "title": doc["title"],
                "status": "FAILED",
                "reason": str(exc),
                "destination": str(destination),
            }
            rows.append(row)

            append_jsonl(
                REJECTED,
                {
                    "timestamp": utc(),
                    "category": "acquisition_failure",
                    **row
                }
            )

            print(f"    FAILED: {exc}")

    if hash_index is not None:
        GLOBAL_HASH_CACHE.write_text(
            json.dumps(hash_index, indent=2, sort_keys=True),
            encoding="utf-8"
        )

    write_report(rows)

    print()
    print("=" * 78)
    print(f"REPORT: {REPORT}")
    print("=" * 78)


if __name__ == "__main__":
    main()

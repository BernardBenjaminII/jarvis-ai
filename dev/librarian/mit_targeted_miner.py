#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, re, time, zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen

UA = "JARVIS-MIT-Targeted-Miner/0.2"

OUT_ROOT = Path("/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/staged/mit_targeted")

MIT_PRESS_OA = "https://mitpress.mit.edu/open-access-at-mit-press/books/"

# High-value OCW starter set. Add more course URLs here over time.
OCW_COURSES = [
    "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/",
    "https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/",
    "https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/",
    "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
    "https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/",
    "https://ocw.mit.edu/courses/6-828-operating-system-engineering-fall-2012/",
    "https://ocw.mit.edu/courses/6-824-distributed-computer-systems-engineering-spring-2006/",
    "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/",
    "https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/",
    "https://ocw.mit.edu/courses/8-02sc-physics-ii-electricity-and-magnetism-fall-2010/",
    "https://ocw.mit.edu/courses/2-003sc-engineering-dynamics-fall-2011/",
    "https://ocw.mit.edu/courses/2-005-thermal-fluids-engineering-i-spring-2013/",
    "https://ocw.mit.edu/courses/16-00-introduction-to-aerospace-engineering-and-design-spring-2003/",
]

GOOD_BOOK_TERMS = [
    "computer", "computing", "algorithm", "software", "artificial intelligence", "ai",
    "machine learning", "robot", "data", "cyber", "network", "biology", "brain",
    "neuroscience", "cognitive", "physics", "quantum", "engineering", "technology",
    "science", "mathematics", "statistics", "medical", "medicine", "health",
    "nuclear", "climate", "energy", "systems"
]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        d = dict(attrs)
        if d.get("href"):
            self.links.append(d["href"])

def fetch(url: str, timeout=45) -> tuple[bytes, str]:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("content-type", "")

def text_from_html(raw: bytes) -> str:
    return re.sub(r"\s+", " ", raw.decode("utf-8", errors="ignore")).strip()

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_name(url: str, fallback="download") -> str:
    name = Path(unquote(urlparse(url).path)).name or fallback
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip()
    return name or fallback

def write_manifest(path: Path, row: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["kind", "source_url", "saved_path", "sha256", "size_bytes", "content_type"])
        w.writerow(row)

def download(url: str, out: Path, kind: str, manifest: Path, require_magic: bytes | None = None) -> bool:
    try:
        data, ctype = fetch(url)
    except Exception as e:
        print(f"[FAIL] {url} :: {e}")
        return False

    if require_magic and not data.startswith(require_magic):
        print(f"[BAD ] wrong magic: {url}")
        return False

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"[SKIP] exists: {out.name}")
        return True

    out.write_bytes(data)
    digest = sha256_file(out)
    write_manifest(manifest, [kind, url, str(out), digest, str(out.stat().st_size), ctype])
    print(f"[OK  ] {out}")
    return True

def mine_ocw_course_zip(course_url: str, out_root: Path, manifest: Path) -> None:
    course = course_url.rstrip("/")
    slug = safe_name(course, "course")
    download_page = course + "/download/"

    print(f"\n[OCW ] {slug}")
    print(f"      {download_page}")

    try:
        raw, _ = fetch(download_page)
    except Exception as e:
        print(f"[FAIL] download page: {e}")
        return

    parser = Links()
    parser.feed(raw.decode("utf-8", errors="ignore"))

    candidates = []
    for href in parser.links:
        full = urljoin(download_page, href)
        low = full.lower()
        if ".zip" in low or "download" in low and ("course" in low or "materials" in low):
            candidates.append(full)

    # Also try common OCW behavior: the download page may redirect/link indirectly.
    candidates = list(dict.fromkeys(candidates))

    if not candidates:
        print("[MISS] no zip link found; saving HTML for inspection")
        html_out = out_root / "ocw_html_debug" / f"{slug}_download.html"
        html_out.parent.mkdir(parents=True, exist_ok=True)
        html_out.write_bytes(raw)
        return

    for link in candidates:
        name = safe_name(link, f"{slug}.zip")
        if not name.lower().endswith(".zip"):
            name = f"{slug}.zip"
        dest = out_root / "ocw_courses" / slug / name
        if download(link, dest, "ocw_course_zip", manifest, require_magic=b"PK"):
            try:
                extract_dir = dest.parent / "extracted"
                extract_dir.mkdir(exist_ok=True)
                with zipfile.ZipFile(dest) as z:
                    z.extractall(extract_dir)
                print(f"[UNZIP] {extract_dir}")
            except Exception as e:
                print(f"[WARN] zip saved but extract failed: {e}")
            break
        time.sleep(1)

def mine_mit_press_books(out_root: Path, manifest: Path, max_books: int) -> None:
    print("\n[MIT PRESS] Open-access books page")
    raw, _ = fetch(MIT_PRESS_OA)
    html = raw.decode("utf-8", errors="ignore")

    parser = Links()
    parser.feed(html)

    book_pages = []
    for href in parser.links:
        full = urljoin(MIT_PRESS_OA, href)
        if "mitpress.mit.edu" in urlparse(full).netloc and "/978" in full:
            if any(term in full.lower() for term in GOOD_BOOK_TERMS) or True:
                book_pages.append(full)

    book_pages = list(dict.fromkeys(book_pages))[:max_books]
    print(f"[FOUND] candidate book pages: {len(book_pages)}")

    for page in book_pages:
        try:
            raw, _ = fetch(page)
        except Exception as e:
            print(f"[FAIL] book page {page} :: {e}")
            continue

        text = text_from_html(raw).lower()
        if not any(t in text for t in GOOD_BOOK_TERMS):
            print(f"[SKIP] low relevance: {page}")
            continue

        p = Links()
        p.feed(raw.decode("utf-8", errors="ignore"))

        pdfs = []
        for href in p.links:
            full = urljoin(page, href)
            if ".pdf" in full.lower():
                pdfs.append(full)

        pdfs = list(dict.fromkeys(pdfs))
        if not pdfs:
            print(f"[MISS] no PDF on book page: {page}")
            continue

        for pdf in pdfs:
            fname = safe_name(pdf, "mit_press_book.pdf")
            if not fname.lower().endswith(".pdf"):
                fname += ".pdf"
            dest = out_root / "mit_press_books" / fname
            download(pdf, dest, "mit_press_open_access_book", manifest, require_magic=b"%PDF-")
            time.sleep(1)

def main():
    ap = argparse.ArgumentParser(description="Targeted MIT miner for JARVIS")
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--mode", choices=["ocw", "press", "all"], default="all")
    ap.add_argument("--max-books", type=int, default=50)
    ap.add_argument("--delay", type=float, default=2.0)
    args = ap.parse_args()

    out = Path(args.out)
    manifest = out / "manifest.csv"
    out.mkdir(parents=True, exist_ok=True)

    if args.mode in {"ocw", "all"}:
        for course in OCW_COURSES:
            mine_ocw_course_zip(course, out, manifest)
            time.sleep(args.delay)

    if args.mode in {"press", "all"}:
        mine_mit_press_books(out, manifest, args.max_books)

    print(f"\nManifest: {manifest}")

if __name__ == "__main__":
    main()

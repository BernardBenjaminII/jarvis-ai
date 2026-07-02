#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, re, time
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

PDF_RE = re.compile(r"\.pdf($|[?#])", re.I)
USER_AGENT = "JARVIS-Knowledge-Hunter/0.1"

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for k, v in attrs:
            if k.lower() == "href" and v:
                self.links.append(v)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch(url: str, timeout: int = 20) -> tuple[bytes, str]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as r:
        ctype = r.headers.get("content-type", "")
        return r.read(), ctype

def safe_filename(url: str) -> str:
    name = Path(unquote(urlparse(url).path)).name or "download.pdf"
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name

def same_domain(url: str, root: str) -> bool:
    return urlparse(url).netloc == urlparse(root).netloc

def robots_allowed(url: str, cache: dict[str, RobotFileParser]) -> bool:
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in cache:
        rp = RobotFileParser()
        rp.set_url(urljoin(base, "/robots.txt"))
        try:
            rp.read()
        except Exception:
            return True
        cache[base] = rp
    return cache[base].can_fetch(USER_AGENT, url)

def crawl(seed: str, out_dir: Path, max_pages: int, max_pdfs: int, delay: float, stay_domain: bool):
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.csv"

    seen_pages, seen_pdfs = set(), set()
    q = deque([seed])
    robots = {}
    downloaded = 0

    with manifest.open("a", newline="", encoding="utf-8") as mf:
        writer = csv.writer(mf)
        if manifest.stat().st_size == 0:
            writer.writerow(["url", "file_path", "sha256", "size_bytes", "content_type"])

        while q and len(seen_pages) < max_pages and downloaded < max_pdfs:
            url = q.popleft()
            if url in seen_pages:
                continue
            if stay_domain and not same_domain(url, seed):
                continue
            if not robots_allowed(url, robots):
                continue

            seen_pages.add(url)
            print(f"[PAGE] {url}")

            try:
                body, ctype = fetch(url)
            except Exception as e:
                print(f"[SKIP] {url} :: {e}")
                continue

            if "html" not in ctype.lower():
                continue

            parser = LinkParser()
            try:
                parser.feed(body.decode("utf-8", errors="ignore"))
            except Exception:
                continue

            for href in parser.links:
                full = urljoin(url, href).split("#")[0]
                if stay_domain and not same_domain(full, seed):
                    continue

                if PDF_RE.search(full):
                    if full in seen_pdfs:
                        continue
                    seen_pdfs.add(full)

                    if not robots_allowed(full, robots):
                        continue

                    print(f"[PDF ] {full}")
                    try:
                        pdf, pdf_ctype = fetch(full)
                    except Exception as e:
                        print(f"[FAIL] {full} :: {e}")
                        continue

                    if not pdf.startswith(b"%PDF-"):
                        print(f"[BAD ] Not a real PDF: {full}")
                        continue

                    fname = safe_filename(full)
                    dest = out_dir / fname
                    n = 1
                    while dest.exists():
                        dest = out_dir / f"{Path(fname).stem}_{n}.pdf"
                        n += 1

                    dest.write_bytes(pdf)
                    digest = sha256_file(dest)
                    writer.writerow([full, str(dest), digest, dest.stat().st_size, pdf_ctype])
                    mf.flush()
                    downloaded += 1
                    print(f"[OK  ] {dest}")

                    if downloaded >= max_pdfs:
                        break
                    time.sleep(delay)
                else:
                    if full not in seen_pages and full.startswith(("http://", "https://")):
                        q.append(full)

            time.sleep(delay)

    print(f"\nDone. Downloaded {downloaded} PDFs.")
    print(f"Manifest: {manifest}")

def main():
    ap = argparse.ArgumentParser(description="Simple reputable PDF crawler for JARVIS")
    ap.add_argument("seed", help="Starting URL")
    ap.add_argument("--out", default="/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/staged")
    ap.add_argument("--max-pages", type=int, default=100)
    ap.add_argument("--max-pdfs", type=int, default=25)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--cross-domain", action="store_true")
    args = ap.parse_args()

    crawl(
        seed=args.seed,
        out_dir=Path(args.out),
        max_pages=args.max_pages,
        max_pdfs=args.max_pdfs,
        delay=args.delay,
        stay_domain=not args.cross_domain,
    )

if __name__ == "__main__":
    main()

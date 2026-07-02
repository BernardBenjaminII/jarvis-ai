#!/usr/bin/env python3
"""
MIT OCW Knowledge Miner
JARVIS Acquisition Engine Pilot

Downloads engineering/science/math/CS PDFs from MIT OCW.

Author: JARVIS
"""

from pathlib import Path
import hashlib
import csv
import requests
import bs4
import re
import time
from urllib.parse import urljoin

BASE = "https://ocw.mit.edu"

SEARCHES = [
    "computer science",
    "artificial intelligence",
    "machine learning",
    "algorithms",
    "operating systems",
    "networking",
    "cybersecurity",

    "mathematics",
    "linear algebra",
    "calculus",
    "probability",
    "statistics",
    "optimization",

    "physics",
    "mechanics",
    "electromagnetics",

    "electrical engineering",
    "electronics",

    "mechanical engineering",
    "thermodynamics",
    "fluid mechanics",

    "robotics",

    "materials science",

    "aerospace",

    "biology",

    "biological engineering",

    "control systems",
]

DOWNLOAD_DIR = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/staged/mit"
)

MANIFEST = DOWNLOAD_DIR / "manifest.csv"

HEADERS = {
    "User-Agent": "JARVIS Knowledge Miner"
}


def sha256(path):

    h = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def search(query):

    url = f"https://ocw.mit.edu/search/?q={query.replace(' ','+')}"

    print(f"\nSearching {query}")

    r = requests.get(url, headers=HEADERS, timeout=30)

    soup = bs4.BeautifulSoup(r.text, "html.parser")

    courses = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/courses/" in href:

            full = urljoin(BASE, href)

            if full not in courses:

                courses.append(full)

    return courses


def mine_course(course):

    print("Course:", course)

    try:

        r = requests.get(course, headers=HEADERS, timeout=30)

    except Exception:

        return

    soup = bs4.BeautifulSoup(r.text, "html.parser")

    pdfs = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if ".pdf" in href.lower():

            pdfs.append(urljoin(BASE, href))

    return pdfs


def download(pdf):

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    name = pdf.split("/")[-1]

    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)

    dest = DOWNLOAD_DIR / name

    if dest.exists():

        return

    try:

        r = requests.get(pdf, headers=HEADERS, timeout=60)

    except Exception:

        return

    if not r.content.startswith(b"%PDF"):

        return

    with open(dest, "wb") as f:

        f.write(r.content)

    digest = sha256(dest)

    with open(MANIFEST, "a", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([pdf, dest, digest])

    print("Downloaded", name)


def main():

    for q in SEARCHES:

        courses = search(q)

        for course in courses:

            pdfs = mine_course(course)

            if not pdfs:

                continue

            for pdf in pdfs:

                download(pdf)

                time.sleep(1)

            time.sleep(2)


if __name__ == "__main__":

    main()

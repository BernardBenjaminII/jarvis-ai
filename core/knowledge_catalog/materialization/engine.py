from __future__ import annotations

import hashlib
import html
import json
import mimetypes
import re
import sqlite3
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from .contracts import MaterializationReport

_TEXT_SUFFIXES = {'.txt','.md','.markdown','.rst','.csv','.tsv','.json','.jsonl','.yaml','.yml','.xml','.html','.htm','.py','.js','.ts','.tsx','.jsx','.css','.scss','.sql','.sh','.bash','.zsh','.ps1','.bat','.ini','.cfg','.conf','.toml','.log'}

@dataclass(frozen=True, slots=True)
class CatalogCandidate:
    file_path: str
    sha256: str
    title: str
    file_type: str

def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (name,)).fetchone() is not None

def migrate_runtime_materialization(conn: sqlite3.Connection) -> None:
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS runtime_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL UNIQUE,
        sha256 TEXT NOT NULL,
        title TEXT NOT NULL,
        media_type TEXT NOT NULL,
        content_text TEXT NOT NULL,
        content_chars INTEGER NOT NULL,
        materialized_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS runtime_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        start_char INTEGER NOT NULL,
        end_char INTEGER NOT NULL,
        token_estimate INTEGER NOT NULL,
        content_sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(document_id, chunk_index),
        FOREIGN KEY(document_id) REFERENCES runtime_documents(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_runtime_chunks_document ON runtime_chunks(document_id);
    CREATE INDEX IF NOT EXISTS idx_runtime_documents_sha256 ON runtime_documents(sha256);
    ''')
    try:
        conn.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS runtime_chunks_fts USING fts5(
            chunk_text, title UNINDEXED, file_path UNINDEXED,
            document_id UNINDEXED, chunk_id UNINDEXED, tokenize='unicode61')''')
    except sqlite3.OperationalError:
        pass

def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8', errors='replace')).hexdigest()

def _clean_html(raw: str) -> str:
    raw = re.sub(r'(?is)<(script|style|noscript).*?>.*?</\\1>', ' ', raw)
    return html.unescape(re.sub(r'\\s+', ' ', re.sub(r'(?s)<[^>]+>', ' ', raw))).strip()

def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception as exc:
            raise RuntimeError('PDF extraction requires pypdf or PyPDF2') from exc
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        value = (page.extract_text() or '').strip()
        if value:
            parts.append(value)
    return '\n\n'.join(parts)

def _docx_xml_text(payload: bytes) -> str:
    root = ET.fromstring(payload)
    paragraphs = []
    for paragraph in root.iter():
        if paragraph.tag.rsplit('}', 1)[-1] != 'p':
            continue
        fragments = []
        for node in paragraph.iter():
            tag = node.tag.rsplit('}', 1)[-1]
            if tag == 't' and node.text:
                fragments.append(node.text)
            elif tag == 'tab':
                fragments.append('\t')
            elif tag in {'br', 'cr'}:
                fragments.append('\n')
        value = ''.join(fragments).strip()
        if value:
            paragraphs.append(value)
    return '\n'.join(paragraphs)

def _read_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if 'word/document.xml' not in names:
                raise ValueError('DOCX package has no word/document.xml part.')
            ordered = ['word/document.xml']
            ordered.extend(sorted(
                name for name in names
                if re.fullmatch(
                    r'word/(?:header\d+|footer\d+|footnotes|endnotes|comments)\.xml',
                    name,
                )
            ))
            parts = []
            for name in ordered:
                value = _docx_xml_text(archive.read(name)).strip()
                if value:
                    parts.append(value)
    except zipfile.BadZipFile as exc:
        raise ValueError('DOCX package is not a valid ZIP container.') from exc
    except ET.ParseError as exc:
        raise ValueError('DOCX contains malformed WordprocessingML.') from exc
    return '\n\n'.join(parts)

def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".epub":
        from core.knowledge_catalog.advanced_extraction.epub import extract_epub
        result = extract_epub(path)
        if isinstance(result, tuple):
            text = result[0] if result else ""
        elif isinstance(result, str):
            text = result
        else:
            text = getattr(result, "text", "")
        text = str(text or "")
        if not text.strip():
            raise ValueError("EPUB extractor produced no usable text.")
        return text
    if suffix == '.pdf':
        return _read_pdf(path)
    if suffix == '.docx':
        return _read_docx(path)
    if suffix not in _TEXT_SUFFIXES:
        raise ValueError(f'Unsupported materialization type: {suffix or "<none>"}')
    raw = path.read_text(encoding='utf-8', errors='replace')
    if suffix in {'.html','.htm'}:
        return _clean_html(raw)
    if suffix == '.json':
        try:
            return json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
        except Exception:
            return raw
    return raw

def chunk_text(text: str, *, target_chars: int = 3200, overlap_chars: int = 320, minimum_chars: int = 120) -> Iterator[tuple[int,int,str]]:
    normalized = text.replace('\r\n','\n').replace('\r','\n').strip()
    if not normalized:
        return
    cursor = 0
    length = len(normalized)
    while cursor < length:
        hard_end = min(length, cursor + target_chars)
        end = hard_end
        if hard_end < length:
            search_start = max(cursor + minimum_chars, hard_end - 700)
            boundary = max(normalized.rfind('\n\n', search_start, hard_end), normalized.rfind('. ', search_start, hard_end), normalized.rfind('\n', search_start, hard_end))
            if boundary > cursor:
                end = boundary + (2 if normalized[boundary:boundary+2] == '. ' else 1)
        value = normalized[cursor:end].strip()
        if len(value) >= minimum_chars or (cursor == 0 and end == length):
            yield cursor, end, value
        if end >= length:
            break
        cursor = max(cursor + 1, end - overlap_chars)

class RuntimeKnowledgeMaterializer:
    def __init__(self, *, database_path: str | Path = DEFAULT_CATALOG_DB, target_chunk_chars: int = 3200, overlap_chars: int = 320) -> None:
        self.database_path = Path(database_path)
        self.target_chunk_chars = max(500, int(target_chunk_chars))
        self.overlap_chars = max(0, min(int(overlap_chars), self.target_chunk_chars // 2))

    def _candidates(self, conn: sqlite3.Connection, *, limit: int | None) -> list[CatalogCandidate]:
        if not _table_exists(conn, 'catalog_documents'):
            raise RuntimeError('catalog_documents table is absent')
        sql = "SELECT file_path, sha256, COALESCE(title,''), COALESCE(file_type,'') FROM catalog_documents ORDER BY file_path"
        params: tuple[object, ...] = ()
        if limit is not None:
            sql += ' LIMIT ?'
            params = (max(0, int(limit)),)
        return [CatalogCandidate(str(r[0]), str(r[1] or ''), str(r[2] or Path(str(r[0])).stem), str(r[3] or '')) for r in conn.execute(sql, params)]

    def _unchanged(self, conn: sqlite3.Connection, candidate: CatalogCandidate) -> bool:
        row = conn.execute('SELECT sha256 FROM runtime_documents WHERE file_path=?', (candidate.file_path,)).fetchone()
        return row is not None and str(row[0]) == candidate.sha256

    def _store(self, conn: sqlite3.Connection, candidate: CatalogCandidate, text: str) -> int:
        media_type = mimetypes.guess_type(candidate.file_path)[0] or f'text/{candidate.file_type or "plain"}'
        conn.execute('''INSERT INTO runtime_documents(file_path,sha256,title,media_type,content_text,content_chars,materialized_at,updated_at)
            VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) DO UPDATE SET sha256=excluded.sha256,title=excluded.title,media_type=excluded.media_type,content_text=excluded.content_text,content_chars=excluded.content_chars,updated_at=CURRENT_TIMESTAMP''',
            (candidate.file_path,candidate.sha256,candidate.title,media_type,text,len(text)))
        document_id = int(conn.execute('SELECT id FROM runtime_documents WHERE file_path=?', (candidate.file_path,)).fetchone()[0])
        conn.execute('DELETE FROM runtime_chunks WHERE document_id=?', (document_id,))
        if _table_exists(conn, 'runtime_chunks_fts'):
            conn.execute('DELETE FROM runtime_chunks_fts WHERE document_id=?', (str(document_id),))
        written = 0
        for index,(start,end,value) in enumerate(chunk_text(text,target_chars=self.target_chunk_chars,overlap_chars=self.overlap_chars)):
            cur = conn.execute('''INSERT INTO runtime_chunks(document_id,chunk_index,chunk_text,start_char,end_char,token_estimate,content_sha256)
                VALUES(?,?,?,?,?,?,?)''', (document_id,index,value,start,end,max(1,len(value)//4),_sha256_text(value)))
            chunk_id = int(cur.lastrowid)
            if _table_exists(conn, 'runtime_chunks_fts'):
                conn.execute('INSERT INTO runtime_chunks_fts(chunk_text,title,file_path,document_id,chunk_id) VALUES(?,?,?,?,?)', (value,candidate.title,candidate.file_path,str(document_id),str(chunk_id)))
            written += 1
        return written

    def materialize(self, *, limit: int | None = None, force: bool = False) -> MaterializationReport:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        materialized = unchanged = skipped = failed = chunks_written = 0
        failures: list[dict[str,str]] = []
        with sqlite3.connect(self.database_path) as conn:
            conn.execute('PRAGMA foreign_keys=ON')
            migrate_runtime_materialization(conn)
            candidates = self._candidates(conn, limit=limit)
            for candidate in candidates:
                path = Path(candidate.file_path)
                if not path.is_file():
                    skipped += 1
                    continue
                if not force and self._unchanged(conn, candidate):
                    unchanged += 1
                    continue
                try:
                    text = extract_text(path).strip()
                    if not text:
                        skipped += 1
                        continue
                    chunks_written += self._store(conn, candidate, text)
                    materialized += 1
                    conn.commit()
                except Exception as exc:
                    conn.rollback()
                    failed += 1
                    failures.append({'file_path': candidate.file_path, 'error': f'{type(exc).__name__}: {exc}'})
        return MaterializationReport(str(self.database_path), len(candidates), materialized, unchanged, skipped, failed, chunks_written, tuple(failures[:100]))

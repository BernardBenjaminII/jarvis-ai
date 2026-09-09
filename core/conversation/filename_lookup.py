"""Read-only catalog identity queries; never infer file presence from passages."""
from __future__ import annotations
import re
import sqlite3
import time
from pathlib import Path

# Deliberately limited to existence/location requests, not content questions.
_REQUEST = re.compile(
    r"(?:can you (?:see|find|locate)|do you have|is there|does .+ exist|"
    r"where is|find|locate|check (?:for|whether))\b", re.I)
_FILE = re.compile(r"(?<![\w/\\])([\w-][\w.-]*\.(?:pdf|txt|md|epub|docx?|html?|csv|zim))(?![\w.])", re.I)
_CONTENT = re.compile(r"\b(?:summari[sz]e|explain|compare|read|delete|remove|move|rename|download|open)\b", re.I)
_TABLES = ('file_assets', 'catalog_documents', 'runtime_documents', 'document_subjects')

def filename_request(query: str) -> str | None:
    text = query.strip()
    matches = list(_FILE.finditer(text))
    if len(matches) != 1 or not _REQUEST.match(text) or _CONTENT.search(text):
        return None
    # Compound requests need the normal orchestrator rather than a partial answer.
    if re.search(r'\b(?:and|then|also)\b|[;\n]', text, re.I):
        return None
    return matches[0].group(1)

def lookup_filename(database_path: str | Path, filename: str) -> dict:
    result = {'filename': filename, 'catalog_path': str(database_path),
              'status': 'unavailable', 'matches': [], 'checked_tables': [],
              'match_rule': 'exact basename, case-insensitive'}
    deadline = time.monotonic() + 8
    try:
        uri = Path(database_path).resolve().as_uri() + '?mode=ro'
        with sqlite3.connect(uri, uri=True, timeout=2) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA query_only=ON')
            conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            conn.create_function('catalog_basename', 1,
                lambda p: str(p or '').replace('\\', '/').rsplit('/', 1)[-1].casefold())
            found = {}
            for table in _TABLES:
                columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
                if 'file_path' not in columns:
                    continue
                selected = ['file_path'] + [c for c in
                    ('id', 'title', 'ingested', 'embedded', 'content_chars', 'verification_status') if c in columns]
                sql = f'SELECT {", ".join(selected)} FROM "{table}" WHERE catalog_basename(file_path)=? LIMIT 101'
                rows = conn.execute(sql, (filename.casefold(),)).fetchall()
                result['checked_tables'].append(table)
                if len(rows) > 100:
                    result['truncated'] = True
                for row in rows[:100]:
                    data = dict(row)
                    path = data.pop('file_path')
                    match = found.setdefault(path, {'path': path, 'records': {}})
                    match['records'][table] = data
            result['matches'] = list(found.values())
            if not result['checked_tables']:
                result['error'] = 'No supported catalog path tables were found.'
            else:
                result['status'] = 'found' if found else 'not_found'
    except (sqlite3.Error, OSError, ValueError) as exc:
        result['error'] = str(exc)
    return result

def render_lookup(result: dict) -> str:
    name = result['filename']
    if result['status'] == 'unavailable':
        return f'I could not complete the catalog lookup for {name}. Its presence is unverified. Details: {result.get("error", "lookup unavailable")}'
    if result['status'] == 'not_found':
        return (f'No exact filename match for {name} was found in the checked catalog tables. '
                'This does not establish whether the file exists on disk or under another name.')
    lines = [f'Yes. The catalog contains {name}.']
    for match in result['matches']:
        lines.append(f"\nPath: {match['path']}")
        records = match['records']
        runtime = records.get('runtime_documents')
        if runtime is not None:
            lines.append(f"Runtime document record: present; extracted characters: {runtime.get('content_chars', 'unknown')}.")
        else:
            lines.append('Runtime document record: no matching path found.' if 'runtime_documents' in result['checked_tables'] else 'Runtime document status: unavailable.')
        asset = records.get('file_assets', {})
        if 'ingested' in asset:
            lines.append(f"Recorded ingestion flag: {asset['ingested']}; embedding flag: {asset.get('embedded', 'unknown')}.")
    if result.get('truncated'):
        lines.append('The result list was truncated.')
    lines.append('\nThese are catalog records; file readability and retrieval quality were not tested.')
    return '\n'.join(lines)

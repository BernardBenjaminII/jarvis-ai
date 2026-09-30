#!/usr/bin/env python3
"""Import source-backed group activity. Python standard library only."""
import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

def now():
    return datetime.now(timezone.utc).isoformat()

def day(value):
    return date.fromisoformat(str(value)[:10]).isoformat()

def point(value):
    if not isinstance(value, dict):
        raise ValueError('Location must be an object')
    for k, limit in [('latitude', 90), ('longitude', 180)]:
        v = value.get(k)
        if isinstance(v, bool) or v is None or v == '':
            raise ValueError(f'Missing {k}')
        n = float(v)
        if not math.isfinite(n) or abs(n) > limit:
            raise ValueError(f'Invalid {k}')
        value[k] = n
    return value

def validate(record):
    r = dict(record)
    if not isinstance(r.get('id'), str) or not r['id']:
        raise ValueError('Record requires stable string id')
    if r.get('kind') not in ('activity', 'presence', 'movement'):
        raise ValueError('Kind must be activity, presence, or movement')
    if not isinstance(r.get('groups'), list) or not r['groups'] or not all(isinstance(x, str) and x.strip() for x in r['groups']):
        raise ValueError('Nonempty group names required')
    r['start'] = day(r.get('start'))
    r['end'] = day(r.get('end', r['start']))
    if r['end'] < r['start']:
        raise ValueError('End precedes start')
    if r.get('published_at'):
        r['published_at'] = day(r['published_at'])
    if r.get('confidence') not in ('unrated', 'low', 'medium', 'high'):
        raise ValueError('Explicit confidence or unrated required')
    sources = r.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('At least one source required')
    for s in sources:
        if not isinstance(s, dict) or not s.get('publisher'):
            raise ValueError('Source publisher required')
        parsed = urlparse(str(s.get('url', '')))
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValueError('Source requires HTTP(S) URL')
    if r['kind'] == 'movement':
        if r.get('movement_basis') not in ('reported', 'inferred') or not str(r.get('evidence', '')).strip():
            raise ValueError('Movement requires explicit basis and supporting evidence')
        r['origin'] = point(dict(r.get('origin', {})))
        r['destination'] = point(dict(r.get('destination', {})))
    else:
        r['location'] = point(dict(r.get('location', {})))
    return r

def ucdp_record(row, names, version):
    groups = [str(row.get(k, '')) for k in ('side_a', 'side_b') if str(row.get(k, '')).casefold() in names]
    if not groups:
        return None
    return validate({
        'id': 'ucdp:' + str(row['id']), 'kind': 'activity', 'groups': sorted(set(groups)),
        'start': row['date_start'], 'end': row['date_end'], 'confidence': 'unrated',
        'title': str(row.get('dyad_name') or 'Reported organized violence'),
        'summary': str(row.get('where_description', '')), 'country': row.get('country', ''),
        'location': {'latitude': row.get('latitude'), 'longitude': row.get('longitude'),
                     'precision': f"UCDP where_prec={row.get('where_prec', 'unknown')}; see codebook"},
        'time_precision': str(row.get('date_prec', 'unknown')),
        'sources': [{'publisher': 'UCDP', 'url': 'https://ucdp.uu.se/downloads/',
                     'reference': str(row.get('source_article', '')), 'version': version}],
        'ingested_at': now(), 'provider': 'ucdp', 'published_at': None,
    })

def acled_record(row, names, version):
    groups = [str(row.get(k, '')) for k in ('actor1', 'actor2') if str(row.get(k, '')).casefold() in names]
    if not groups:
        return None
    event_date = str(row['event_date'])
    try:
        event_date = day(event_date)
    except ValueError:
        event_date = datetime.strptime(event_date, '%d %B %Y').date().isoformat()
    return validate({
        'id': 'acled:' + str(row['event_id_cnty']), 'kind': 'activity', 'groups': sorted(set(groups)),
        'start': event_date, 'end': event_date, 'confidence': 'unrated',
        'title': str(row.get('sub_event_type') or row.get('event_type') or 'Reported activity'),
        'summary': str(row.get('notes', '')), 'country': row.get('country', ''),
        'location': {'latitude': row.get('latitude'), 'longitude': row.get('longitude'),
                     'precision': f"ACLED geo_precision={row.get('geo_precision', 'unknown')}; see codebook"},
        'time_precision': str(row.get('time_precision', 'unknown')),
        'sources': [{'publisher': 'ACLED', 'url': 'https://acleddata.com/',
                     'reference': str(row.get('source', '')), 'version': version}],
        'ingested_at': now(), 'provider': 'acled', 'published_at': None,
    })

def save(records, output, source):
    records = [validate(r) for r in records]  # Complete validation before touching output.
    output = Path(output)
    existing = json.loads(output.read_text()) if output.exists() else {'records': [], 'sources': []}
    if existing.get('schema_version', 1) != 1:
        raise ValueError('Unsupported existing schema')
    merged = {r['id']: validate(r) for r in existing['records']}
    for r in records:
        merged[r['id']] = r
    state = {'schema_version': 1, 'generated_at': now(),
             'records': sorted(merged.values(), key=lambda r: (r['start'], r['id'])),
             'sources': (existing.get('sources', []) + [source])[-100:]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent, delete=False) as f:
        json.dump(state, f, ensure_ascii=False, indent=2, allow_nan=False)
        temp = Path(f.name)
    temp.chmod(0o644)
    temp.replace(output)
    print(f'Imported {len(records)} records; {len(merged)} total. Output: {output}')

def fetch_ucdp(version, actors, start, end):
    if not re.fullmatch(r'\d+(?:\.\d+){1,4}', version):
        raise ValueError('Invalid UCDP version')
    token = os.environ.get('UCDP_API_TOKEN')
    if not token:
        raise ValueError('Set UCDP_API_TOKEN (request access through https://ucdp.uu.se/apidocs/) or use a downloaded CSV.')
    rows = []
    page = 1
    while True:
        query = urlencode({'Actor': ','.join(map(str, actors)), 'StartDate': start,
                           'EndDate': end, 'pagesize': 1000, 'page': page})
        url = f'https://ucdpapi.pcr.uu.se/api/gedevents/{version}?{query}'
        request = Request(url, headers={'x-ucdp-access-token': token, 'Accept': 'application/json',
                                       'User-Agent': 'JarvisGroupActivity/1.0'})
        with urlopen(request, timeout=45) as response:
            batch = json.load(response)
        rows.extend(batch['Result'])
        pages = int(batch['TotalPages'])
        if page >= pages:
            break
        if page >= 1000:
            raise ValueError('Page limit reached; narrow the date range. Nothing saved.')
        page += 1
    return rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(__file__).resolve().parents[1] / 'core/src/static/global_3d/group_activity/events.json'
    parser.add_argument('--output', type=Path, default=default)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('ucdp-csv', 'acled-csv'):
        p = sub.add_parser(name)
        p.add_argument('file', type=Path)
        p.add_argument('--group', action='append', required=True, help='Exact provider actor name; repeat for multiple groups')
        p.add_argument('--version', required=True, help='Dataset version or export date')
    p = sub.add_parser('evidence-json')
    p.add_argument('file', type=Path, help='JSON array of reviewed normalized records')
    p = sub.add_parser('ucdp-sync')
    p.add_argument('--version', required=True)
    p.add_argument('--actor-id', type=int, action='append', required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'evidence-json':
            records = json.loads(args.file.read_text())
            if not isinstance(records, list):
                raise ValueError('Expected JSON array')
        elif args.command == 'ucdp-sync':
            start, end = day(args.start), day(args.end)
            if end < start:
                raise ValueError('End precedes start')
            rows = fetch_ucdp(args.version, args.actor_id, start, end)
            ids = set(args.actor_id)
            names = {str(row.get(side, '')).casefold() for row in rows for side in ('side_a', 'side_b')
                     if int(row.get(side + '_new_id') or -1) in ids}
            records = [ucdp_record(r, names, args.version) for r in rows]
        else:
            names = {n.casefold() for n in args.group}
            fn = ucdp_record if args.command == 'ucdp-csv' else acled_record
            with args.file.open(encoding='utf-8-sig', newline='') as f:
                records = [fn(r, names, args.version) for r in csv.DictReader(f)]
        records = [r for r in records if r is not None]
        if not records:
            raise ValueError('No matching records. Existing output unchanged; check exact group names, IDs, and dates.')
        save(records, args.output, {'import': args.command, 'at': now(), 'records': len(records),
                                   'version': getattr(args, 'version', None)})
    except Exception as exc:
        parser.exit(1, f'Import failed; output not replaced: {exc}\n')

if __name__ == '__main__':
    main()

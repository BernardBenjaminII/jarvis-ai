"""Bounded public security feeds. Classification is a triage hint, not verification."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
import json
import math
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

UN_URL = 'https://news.un.org/feed/subscribe/en/news/topic/peace-and-security/feed/rss.xml'
CERT_URL = 'https://cert.europa.eu/publications/security-advisories-rss'
KEV_URL = 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'
MAX_BYTES = 8 * 1024 * 1024
PHYSICAL = re.compile(r'\b(conflict|war|attack\w*|strike\w*|ceasefire|military|missile\w*|drone\w*|armed|violence|hostilities|fighting|terror\w*|siege|blockade|displacement|peacekeep\w*|nuclear|unrest|escalat\w*)\b', re.I)
CYBER = re.compile(r'\b(exploit\w*|ransomware|breach\w*|zero.day|actively|in.the.wild|remote code execution|critical|malware|espionage)\b', re.I)

def clean(value):
    return ' '.join(unescape(re.sub(r'<[^>]*>', ' ', str(value or ''))).split())

def date(value):
    try:
        result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        try: result = parsedate_to_datetime(str(value))
        except (ValueError, TypeError, OverflowError): return None
    return result.replace(tzinfo=result.tzinfo or timezone.utc).astimezone(timezone.utc)

def canonical_url(value, host=None):
    try:
        parsed = urlsplit(str(value))
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password: return None
        if host and parsed.hostname != host: return None
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ''))
    except ValueError: return None

def group_reports(records, now=None):
    """
    Merge repeated URLs/exact normalized headlines only; never infer
    corroboration.

    R8.2 adds:
      - category-aware retention
      - a larger normalized event pool
      - deterministic display-priority scoring

    fusion_score is a presentation/triage value only. It is not a
    verification score, intelligence-confidence judgment, or claim
    that an event is independently corroborated.
    """
    now = now or datetime.now(timezone.utc)

    groups = {}
    aliases = {}

    retention_days = {
        'aviation': 365,
        'maritime': 365,
        'reference': 365,
        'physical': 90,
        'military': 90,
        'cyber': 90,
        'disaster': 30,
    }

    severity_weight = {
        'critical': 400,
        'extreme': 400,
        'severe': 400,
        'high': 300,
        'major': 300,
        'medium': 200,
        'moderate': 200,
        'watch': 150,
        'low': 100,
        'info': 50,
    }

    # Small domain weights prevent massive feeds from receiving an
    # accidental advantage purely from volume. They do not express
    # strategic importance.
    domain_weight = {
        'physical': 35,
        'military': 35,
        'aviation': 30,
        'maritime': 30,
        'cyber': 20,
        'disaster': 10,
        'reference': 0,
    }

    for original in records:
        stamp = date(original.get('published_at'))

        if not stamp:
            continue

        category = str(
            original.get('category') or 'physical'
        ).lower()

        max_age = retention_days.get(category, 90)

        if (
            stamp < now - timedelta(days=max_age)
            or stamp > now + timedelta(days=1)
        ):
            continue

        item = dict(original)

        title = str(item.get('title') or '').strip()

        if not title:
            continue

        title_key = (
            category,
            re.sub(
                r'\W+',
                ' ',
                title.lower()
            ).strip(),
        )

        source = item.get('source') or {}
        source_url = source.get('url')

        url_key = (
            canonical_url(source_url)
            if source_url
            else None
        )

        key = None

        if url_key:
            key = aliases.get(('url', url_key))

        if key is None:
            key = aliases.get(('title', title_key))

        if key is None:
            key = (
                item.get('id')
                or f"{category}:{title_key[1]}"
            )

        if url_key:
            aliases[('url', url_key)] = key

        aliases[('title', title_key)] = key

        if key not in groups:
            item['sources'] = (
                [source]
                if source
                else []
            )

            item['report_count'] = 1

            item['age_hours'] = max(
                0,
                (now - stamp).total_seconds() / 3600,
            )

            groups[key] = item

        else:
            existing = groups[key]

            if (
                source
                and source not in existing['sources']
            ):
                existing['sources'].append(source)
                existing['report_count'] += 1

            if (
                existing.get('operational_state') == 'STALE'
                and item.get('operational_state') == 'LIVE'
            ):
                existing['operational_state'] = 'LIVE'

        groups[key]['verification'] = (
            'Publisher report; not independently verified by JARVIS'
        )

    events = list(groups.values())

    for item in events:
        severity = str(
            item.get('severity') or 'watch'
        ).lower()

        category = str(
            item.get('category') or 'physical'
        ).lower()

        age_hours = float(
            item.get('age_hours') or 0
        )

        # Recency contributes 0–100 points and decays across
        # approximately 30 days.
        recency_score = max(
            0.0,
            100.0 - (
                age_hours / (24.0 * 30.0)
            ) * 100.0,
        )

        source_count = max(
            1,
            len(item.get('sources') or []),
        )

        # This rewards multiple publisher records only as a queue
        # ordering signal. It does NOT claim independent confirmation.
        publisher_bonus = min(
            30,
            max(0, source_count - 1) * 10,
        )

        fusion_score = (
            severity_weight.get(severity, 100)
            + domain_weight.get(category, 0)
            + recency_score
            + publisher_bonus
        )

        item['fusion_score'] = round(
            fusion_score,
            2,
        )

        item['fusion_basis'] = {
            'severity': severity,
            'category': category,
            'age_hours': round(age_hours, 1),
            'publisher_count': source_count,
        }

    events.sort(
        key=lambda item: (
            float(item.get('fusion_score') or 0),
            item.get('published_at') or '',
        ),
        reverse=True,
    )

    # Normalized pool. The Executive UI will project a much smaller
    # balanced subset from this collection.
    return events[:500]

class SecurityFeed:
    def __init__(self, provider_id, publisher, url, category, *, opener=urlopen, clock=None):
        self.provider_id, self.publisher, self.url, self.category = provider_id, publisher, url, category
        self._opener = opener
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def collect(self):
        request = Request(self.url, headers={'User-Agent':'JARVIS-SITREP/6.0', 'Accept':'application/rss+xml,application/xml,application/json'})
        with self._opener(request, timeout=12) as response:
            raw = response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ValueError('Security feed exceeds size limit')
        return self.parse(raw)

    def result(self, items):
        return dict(provider_id=self.provider_id, publisher=self.publisher, feed_url=self.url,
                    retrieved_at=self._clock().isoformat(), security_events=items)

    def record(self, title, summary, url, published, *, priority='watch', reason='', location=None):
        return dict(id=self.provider_id+'-'+sha256(url.encode()).hexdigest()[:20], kind='security_event',
                    category=self.category, title=title[:300], summary=summary[:900], published_at=published.isoformat(),
                    severity=priority, priority_reason=reason, location=location,
                    region='Source coordinates' if location else 'Location unspecified / multi-region',
                    operational_state='LIVE', classification='SECURITY REPORT',
                    source=dict(provider_id=self.provider_id, publisher=self.publisher, authority='publisher',
                                retrieved_at=self._clock().isoformat(), url=url))

    def parse(self, raw):
        if len(raw)>MAX_BYTES: raise ValueError('Security feed exceeds size limit')
        if re.search(br'<!\s*(DOCTYPE|ENTITY)', raw, re.I): raise ValueError('XML declarations not allowed')
        root = ET.fromstring(raw)
        if root.tag.split('}')[-1] not in ('rss', 'feed', 'RDF'): raise ValueError('Not a recognized news feed')
        entries = root.findall('.//item') + root.findall('{http://www.w3.org/2005/Atom}entry')
        items=[]
        for entry in entries[:250]:
            values={child.tag.split('}')[-1]: child for child in entry}
            def text(name):
                element=values.get(name)
                return ''.join(element.itertext()) if element is not None else ''
            title, summary = clean(text('title')), clean(text('description') or text('summary') or text('content'))
            link=values.get('link')
            url=canonical_url((link.get('href') or link.text or '') if link is not None else '', urlsplit(self.url).hostname)
            published=date(text('pubDate') or text('published') or text('updated') or text('date'))
            if not title or not url or not published: continue
            if not self._clock()-timedelta(days=30) <= published <= self._clock()+timedelta(days=1): continue
            terms=(PHYSICAL if self.category=='physical' else CYBER).findall(title+' '+summary)
            if not terms: continue
            location=None
            point=entry.find('{http://www.georss.org/georss}point')
            if point is not None:
                try:
                    lat,lon=map(float, (point.text or '').split())
                    if math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180:
                        location={'latitude':lat,'longitude':lon}
                except ValueError: pass
            items.append(self.record(title,summary,url,published,reason='Topic match: '+', '.join(sorted(set(t.lower() for t in terms))[:5]),location=location))
        if not entries: raise ValueError('Feed has no recognizable entries')
        return self.result(items)

class KevFeed(SecurityFeed):
    def __init__(self, **kwargs):
        super().__init__('cisa_kev','CISA Known Exploited Vulnerabilities',KEV_URL,'cyber',**kwargs)

    def collect(self):
        try:
            return super().collect()
        except Exception as primary_error:
            mirror='https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json'
            request=Request(mirror,headers={'User-Agent':'JARVIS-SITREP/6.0','Accept':'application/json'})
            with self._opener(request,timeout=12) as response:
                raw=response.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES: raise ValueError('KEV mirror exceeds size limit')
            result=self.parse(raw)
            result['feed_url']=mirror
            result['transport_note']='Official CISA mirror; primary endpoint failed: '+type(primary_error).__name__
            for item in result['security_events']: item['source']['feed_url']=mirror
            return result

    def parse(self, raw):
        payload=json.loads(raw)
        if not isinstance(payload,dict) or not isinstance(payload.get('vulnerabilities'),list): raise ValueError('Unrecognized KEV catalog')
        items=[]
        for row in payload['vulnerabilities']:
            cve=str(row.get('cveID',''))
            published=date(row.get('dateAdded'))
            if not re.fullmatch(r'CVE-\d{4}-\d{4,}',cve) or not published: continue
            if not self._clock()-timedelta(days=30)<=published<=self._clock()+timedelta(days=1): continue
            # dateAdded is catalog publication, not the date an attack began.
            url='https://www.cisa.gov/known-exploited-vulnerabilities-catalog?search_api_fulltext='+cve
            item=self.record(cve+' · '+clean(row.get('vulnerabilityName')),clean(row.get('shortDescription')),url,published,
                             priority='high',reason='CISA catalog lists evidence of exploitation; not evidence your systems are affected')
            item.update(cve=cve, date_label='Added to KEV catalog', action=clean(row.get('requiredAction')),
                        classification='KNOWN EXPLOITED VULNERABILITY', region='Global / affected products',location=None)
            item['source']['authority']='primary'
            items.append(item)
        return self.result(items)

def default_security_providers():
    return (SecurityFeed('un_peace_security','UN News',UN_URL,'physical'),
            SecurityFeed('cert_eu_advisories','CERT-EU',CERT_URL,'cyber'), KevFeed())

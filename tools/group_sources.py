#!/usr/bin/env python3
"""Public-source discovery and UCDP refresh for the installed Jarvis R1 layer."""
import argparse
import csv
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import hashlib
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode, unquote
from urllib.error import HTTPError
from urllib.request import Request, urlopen

UCDP = 'https://ucdp.uu.se/downloads/'
CTP = 'https://www.criticalthreats.org/analysis/africa-file'
UN = 'https://main.un.org/securitycouncil/en/sanctions/1267/monitoring-team/reports'
ALIASES = {'IS':['Islamic State','ISIS','ISIL','Daesh'], 'JNIM':['JNIM'],
           'Al-Shabaab':['Al-Shabaab','al Shabaab'], 'TTP':['TTP','Tehrik-i-Taliban','Tehreek-e-Taliban'],
           'JAS':['Boko Haram','Jamaatu Ahlis Sunna'], 'AQAP':['AQAP','al Qaeda in the Arabian Peninsula']}
CADENCE = {'ucdp':86400, 'gdelt':3600, 'critical_threats':21600, 'un_monitoring':86400}
RSS_FEEDS = {
    'bbc_world':('BBC News', 'https://feeds.bbci.co.uk/news/world/rss.xml'),
    'france24_africa':('France 24', 'https://www.france24.com/en/africa/rss'),
    'dw_world':('DW', 'https://rss.dw.com/rdf/rss-en-world'),
    'un_news_security':('UN News', 'https://news.un.org/feed/subscribe/en/news/topic/peace-and-security/feed/rss.xml'),
}
CADENCE.update({key:3600 for key in RSS_FEEDS})
TOPICS=re.compile(r'\b(?:terror\w*|militant\w*|insurgen\w*|jihad\w*|extremis\w*|armed groups?|sahel|boko haram|al[- ]qa[ei]da|islamic state|isis|isil|daesh|jnim|al[- ]shabaab|ttp|aqap)\b',re.I)

class SourceAccessError(ValueError):
    pass

def retry_seconds(value, current):
    try: return max(0,float(value))
    except (TypeError,ValueError):
        try: return max(0,parsedate_to_datetime(value).timestamp()-current)
        except (TypeError,ValueError,OverflowError): return 0

def failure_status(exc, prior, current):
    count=prior.get('consecutive_failures',0)+1
    code=getattr(exc,'code',None)
    if code==429:
        delay=max(min(21600*2**min(count-1,3),86400),retry_seconds(exc.headers.get('Retry-After') if exc.headers else None,current))
        state='RATE_LIMITED'
    elif code==403 or isinstance(exc,SourceAccessError):
        delay=86400;state='ACCESS_DENIED'
    else:
        delay=3600;state='ERROR'
    return {'state':state,'consecutive_failures':count,'next_retry_epoch':current+delay,
            'next_retry_at':datetime.fromtimestamp(current+delay,timezone.utc).isoformat(),
            'error':f'{type(exc).__name__}: {exc}',
            'note':'Previous records retained. Provider cooldown applies even with --force.'}

def utc():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default

def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        tmp = Path(f.name)
    tmp.chmod(0o644)
    tmp.replace(path)

def fetch(url, limit=80_000_000):
    req = Request(url, headers={'User-Agent':'JarvisPublicSourceReader/2.0', 'Accept':'application/json,text/csv,text/html'})
    with urlopen(req, timeout=25) as response:
        data = response.read(limit + 1)
        if response.status==202 and (b'awswaf.com' in data or b'not a robot' in data.lower()):
            raise SourceAccessError('Provider returned a JavaScript verification page (HTTP 202); no feed was collected')
    if len(data) > limit:
        raise ValueError('Source response exceeds configured size limit')
    return data

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]; self.href=None; self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href=dict(attrs).get('href'); self.parts=[]
    def handle_data(self, data):
        if self.href is not None: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.items.append((self.href,' '.join(' '.join(self.parts).split())))
            self.href=None; self.parts=[]

def links(raw):
    parser=Links(); parser.feed(raw.decode('utf-8-sig')); return parser.items

def canonical(url):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:
        raise ValueError('Invalid report URL')
    pairs=[(k,v) for k,v in parse_qsl(p.query, keep_blank_values=True)
           if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')]
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',urlencode(sorted(pairs)),''))

def report(url, title, provider, publisher, **extra):
    url=canonical(url)
    tags=[group for group,names in ALIASES.items() if any(re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',title,re.I) for n in names)]
    return {'id':hashlib.sha256(url.encode()).hexdigest()[:24], 'url':url,
            'title':title, 'provider':provider,'publisher':publisher,'groups':tags,
            'review_state':'unreviewed','first_seen':utc(),'last_seen':utc(),
            'published_at':None,'independence':'not assessed', **extra}

def merge_reports(old, fresh):
    merged={r['id']:dict(r) for r in old}
    for row in fresh:
        previous=merged.get(row['id'],{})
        row=dict(row)
        row['first_seen']=previous.get('first_seen',row['first_seen'])
        row['review_state']=previous.get('review_state','unreviewed')
        row['found_via']=sorted(set(previous.get('found_via',[previous.get('provider')]) + [row['provider']])-{None})
        merged[row['id']]={**previous,**row}
    # Preserve older reports on disk; the UI limits its rendered list.
    return sorted(merged.values(),key=lambda r:r['first_seen'],reverse=True)

def gdelt():
    query='('+' OR '.join('"'+n+'"' for names in ALIASES.values() for n in names)+')'
    url='https://api.gdeltproject.org/api/v2/doc/doc?'+urlencode({
        'query':query,'mode':'artlist','format':'json','maxrecords':250,'timespan':'7d','sort':'datedesc'})
    data=json.loads(fetch(url,5_000_000))
    if not isinstance(data,dict) or not isinstance(data.get('articles'),list):
        raise ValueError('GDELT returned an unexpected response')
    rows=[]
    for a in data['articles']:
        if not a.get('url') or not a.get('title'): continue
        rows.append(report(a['url'],a['title'],'gdelt',a.get('domain') or urlsplit(a['url']).hostname,
                           gdelt_seen_at=a.get('seendate'),language=a.get('language')))
    return rows, f'{len(rows)} article links; capped at 250; last 7 days; not exhaustive'

def local_tag(node):
    return node.tag.rsplit('}',1)[-1]

def child_text(node, names):
    for child in node:
        if local_tag(child) in names:
            return ''.join(child.itertext()).strip()
    return ''

def plain(value):
    class Text(HTMLParser):
        def __init__(self):super().__init__();self.parts=[]
        def handle_data(self,data):self.parts.append(data)
    parser=Text();parser.feed(value)
    return ' '.join(' '.join(parser.parts).split())

def publication(value):
    if not value:return None
    try:dt=parsedate_to_datetime(value)
    except (ValueError,TypeError):
        try:dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:return None
    if dt.tzinfo is None:return None
    return dt.astimezone(timezone.utc).isoformat()

def parse_feed(raw, provider, publisher, url):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('XML declarations are not supported')
    root=ET.fromstring(raw)
    if local_tag(root) not in ('rss','RDF','feed'):
        raise ValueError('Expected RSS/Atom XML, received a different document')
    items=[node for node in root.iter() if local_tag(node) in ('item','entry')]
    if not items:raise ValueError('Feed contains no entries; cannot establish feed health')
    rows=[];dates=[];undated=0
    for item in items:
        title=plain(child_text(item,{'title'}))
        summary=plain(child_text(item,{'description','summary','content','encoded'}))
        published=publication(child_text(item,{'pubDate','published','date'}))
        if published:dates.append(published)
        else:undated+=1
        if not TOPICS.search(title+' '+summary):continue
        link=''
        for node in item:
            if local_tag(node)=='link' and node.attrib.get('rel','alternate')=='alternate':
                link=node.attrib.get('href') or (node.text or '').strip()
                if link:break
        if not link or not title:continue
        full=urljoin(url,link)
        try:r=report(full,title,provider,publisher,published_at=published)
        except ValueError:continue
        r['discovery_basis']='Security-topic keyword match in publisher feed; not verified group attribution'
        rows.append(r)
    latest=max(dates) if dates else None
    # A reachable feed is not necessarily a current one.
    freshness='unknown publication freshness'
    if latest:
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(latest)).total_seconds()/86400
        freshness=f'newest published {latest}'
        if age>14:freshness='STALE FEED (>14 days); '+freshness
        if age < -1:freshness='FUTURE-DATED FEED; '+freshness
    return rows,f'{len(items)} feed entries; {len(rows)} security-topic matches; {freshness}; {undated} without publication dates'

def rss(provider):
    publisher,url=RSS_FEEDS[provider]
    return parse_feed(fetch(url,5_000_000),provider,publisher,url)

def ctp_from_html(raw):
    rows=[]
    for href,title in links(raw):
        url=urljoin(CTP,href)
        if urlsplit(url).hostname not in ('www.criticalthreats.org','criticalthreats.org'): continue
        if '/analysis/' not in url or canonical(url)==canonical(CTP): continue
        if 'africa file' not in title.casefold(): continue
        rows.append(report(url,title,'critical_threats','Critical Threats Project'))
    if not rows: raise ValueError('No Africa File links found; page may be blocked or its layout changed')
    return rows

def un_from_html(raw):
    page=raw.decode('utf-8-sig',errors='replace')
    title_match=re.search(r'<title[^>]*>(.*?)</title>',page,re.I|re.S)
    title=' '.join(title_match.group(1).split())[:160] if title_match else '(no HTML title)'
    if any(marker in title.casefold() for marker in ('access denied','forbidden','request rejected','just a moment','captcha')):
        raise SourceAccessError(f'UN returned an access/challenge page: {title}')
    rows=[]
    anchors=links(raw);official_count=0
    for href,label in anchors:
        url=urljoin(UN,href)
        if urlsplit(url).hostname not in ('docs.un.org','undocs.org','www.undocs.org','documents.un.org'): continue
        official_count+=1
        symbol=re.search(r'S/\d{4}/\d+(?:/Rev\.\d+)?',unquote(url),re.I)
        if 'report' not in label.casefold() and not symbol: continue
        rows.append(report(url,label or f'UN document {symbol.group(0)}','un_monitoring','UN Security Council Monitoring Team'))
    if not rows:
        raise ValueError(f'UN response contained no recognized report links; title={title!r}; bytes={len(raw)}; anchors={len(anchors)}; official_document_links={official_count}. This response needs inspection; not evidence of an empty report archive.')
    return rows

def dataset_links(raw, since_year):
    found={}
    for href,_ in links(raw):
        url=urljoin(UCDP,href); p=urlsplit(url)
        m=re.search(r'/candidateged/GEDEvent_v(\d{2}(?:_\d{1,2}){2,3})\.csv$',p.path)
        if p.hostname!='ucdp.uu.se' or not m: continue
        nums=tuple(map(int,m.group(1).split('_')))
        if nums[0]+2000 < since_year: continue
        # Chronological end of release period; H1 before July before August.
        key=(nums[-2]+2000,nums[-1]) if len(nums)==4 else (nums[0]+2000,nums[-1])
        found[url]=(key,m.group(1).replace('_','.'))
    if not found: raise ValueError('No supported UCDP candidate CSV links found')
    return [(url,version) for url,(_,version) in sorted(found.items(),key=lambda x:x[1][0])]

def ucdp(repo, state, config):
    path=repo/'tools/group_activity.py'
    spec=importlib.util.spec_from_file_location('jarvis_activity_import',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    releases=dataset_links(fetch(UCDP,5_000_000),config['since_year'])
    hashes=dict(state.get('dataset_hashes',{})); incoming={}
    selected={g.casefold() for g in config['groups']}
    changed=0
    for url,version in releases:
        raw=fetch(url); digest=hashlib.sha256(raw).hexdigest()
        # Refetch daily to pick up corrections; avoid reimport if unchanged.
        config_key=hashlib.sha256(json.dumps(sorted(selected)).encode()).hexdigest()
        signature=digest+':'+config_key
        is_changed=hashes.get(url)!=signature
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        required={'id','side_a','side_b','date_start','date_end','latitude','longitude'}
        if not required.issubset(set(reader.fieldnames or [])): raise ValueError('Unexpected UCDP CSV columns')
        for row in reader:
            record=module.ucdp_record(row,selected,version)
            if record:
                record['sources'][0].update(url=url,license='CC BY 4.0',citation='Hegre et al. (2020), Introducing the UCDP Candidate Events Dataset, Research & Politics')
                incoming[record['id']]=record
        hashes[url]=signature; changed+=int(is_changed)
    output=repo/'core/src/static/global_3d/group_activity/events.json'
    if incoming and (changed or not output.exists()):
        module.save(list(incoming.values()),output,{'import':'ucdp-public-csv-r2','at':utc(),'datasets':changed})
    state['dataset_hashes']=hashes
    return f'{changed} changed releases; {len(incoming)} matching activity records checked; source reporting remains delayed'

def run(repo, config, force=False, only=None):
    static=repo/'core/src/static/global_3d/group_activity'
    work=repo/'artifacts/group_sources_r2'; work.mkdir(parents=True,exist_ok=True)
    with (work/'updater.lock').open('w') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError('Another source update is already running')
        state=read_json(work/'state.json',{'sources':{}})
        inbox=read_json(static/'reports.json',{'schema_version':1,'reports':[],'sources':{}})
        failures=0
        for provider,period in CADENCE.items():
            if only and provider not in only: continue
            prior=state['sources'].get(provider,{})
            if provider in config.get('disabled_sources',[]):
                state['sources'][provider]={**prior,'state':'PAUSED','note':'Paused in config/group_sources_r2.json; no request sent', 'error':None}
                print(f'{provider}: PAUSED — no request sent',flush=True)
                inbox.update(generated_at=utc(),sources=state['sources'])
                atomic_json(static/'reports.json',inbox);atomic_json(work/'state.json',state)
                continue
            # Respect failures already recorded by R2 when upgrading.
            if not prior.get('next_retry_epoch') and prior.get('state')=='ERROR':
                old_error=prior.get('error','')
                code=429 if 'HTTP Error 429' in old_error else 403 if 'HTTP Error 403' in old_error else None
                if code:
                    prior={**prior,**failure_status(HTTPError('',code,old_error,{},None),prior,prior.get('attempt_epoch',time.time()))}
                    state['sources'][provider]=prior
            if time.time()<prior.get('next_retry_epoch',0):
                failures+=1
                print(f"{provider}: {prior['state']} — no request sent; next retry {prior['next_retry_at']}",flush=True)
                inbox.update(generated_at=utc(),sources=state['sources'])
                atomic_json(static/'reports.json',inbox);atomic_json(work/'state.json',state)
                continue
            interval=min(period,3600) if prior.get('state')=='ERROR' else period
            if not force and time.time()-prior.get('attempt_epoch',0)<interval: continue
            status={**prior,'attempted_at':utc(),'attempt_epoch':time.time(),'cadence_hours':period/3600}
            print(f'Checking {provider}...',flush=True)
            try:
                if provider=='ucdp': note=ucdp(repo,state,config)
                else:
                    if provider in RSS_FEEDS:fresh,note=rss(provider)
                    elif provider=='gdelt': fresh,note=gdelt()
                    elif provider=='critical_threats':
                        fresh=ctp_from_html(fetch(CTP,5_000_000))
                        # The series index can lag the publisher's front page.
                        try: fresh+=ctp_from_html(fetch('https://www.criticalthreats.org/',5_000_000))
                        except Exception: pass
                        note=f'{len({r["id"] for r in fresh})} Africa File links'
                    else:
                        fresh=un_from_html(fetch(UN,5_000_000)); note=f'{len(fresh)} UN report links, including historical reports'
                    inbox['reports']=merge_reports(inbox['reports'],fresh)
                status.update(state='OK',last_success=utc(),note=note,error=None,consecutive_failures=0,next_retry_epoch=0,next_retry_at=None)
            except Exception as exc:
                failures+=1
                status.update(failure_status(exc,prior,time.time()))
            state['sources'][provider]=status
            print(f"{provider}: {status['state']} — {status.get('error') or status['note']}",flush=True)
            inbox.update(generated_at=utc(),sources=state['sources'])
            atomic_json(static/'reports.json',inbox)
            atomic_json(work/'state.json',state)
        return failures

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--force',action='store_true',help='Ignore normal check intervals; never override failure cooldowns')
    p.add_argument('--only',choices=list(CADENCE),action='append')
    a=p.parse_args(); repo=a.repo.resolve()
    if not (repo/'tools/group_activity.py').exists(): p.exit(1,'Install Group Activity R1 first.\n')
    config=read_json(repo/'config/group_sources_r2.json',{'groups':list(ALIASES),'since_year':2026})
    try: failures=run(repo,config,a.force,a.only)
    except Exception as exc: p.exit(1,f'Updater stopped: {exc}\n')
    p.exit(2 if failures else 0)

if __name__=='__main__': main()

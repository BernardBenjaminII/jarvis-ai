from __future__ import annotations
import hashlib, json
from collections import defaultdict
from dataclasses import replace
from .contracts import DEFAULT_SECTION_ORDER
from .models import ConstitutionalSection

def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def build_sections(articles):
    grouped=defaultdict(list)
    for article in articles: grouped[article.domain or "general"].append(article)
    order={domain:i for i,domain in enumerate(DEFAULT_SECTION_ORDER)}
    domains=sorted(grouped,key=lambda d:(order.get(d,len(order)),d))
    mapping={}
    sections=[]
    for i,domain in enumerate(domains,1):
        sid=f"SECTION-{i:03d}"
        mapping[domain]=sid
        ids=tuple(sorted(a.article_id for a in grouped[domain]))
        sections.append(ConstitutionalSection(
            section_id=sid,title=domain.replace("_"," ").replace("-"," ").title() or "General",
            domain=domain,article_ids=ids,fingerprint=_hash({"section_id":sid,"domain":domain,"article_ids":ids}),
        ))
    return tuple(replace(a,section_id=mapping[a.domain or "general"]) for a in articles),tuple(sections)

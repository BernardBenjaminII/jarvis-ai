from __future__ import annotations
from collections import defaultdict
from .models import ClaimEvidence

class UnionFind:
    def __init__(self, ids): self.parent = {x:x for x in ids}
    def find(self, x):
        if self.parent[x] != x: self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return
        winner, loser = sorted((ra, rb))
        self.parent[loser] = winner

def build_clusters(claims: tuple[ClaimEvidence,...], relationships: tuple[dict,...]):
    by_id = {c.claim_id:c for c in claims}
    uf = UnionFind(tuple(sorted(by_id)))
    for edge in relationships:
        if str(edge.get("relationship_type","")) in {"duplicates","supports","refines"}:
            a, b = str(edge.get("source_claim_id","")), str(edge.get("target_claim_id",""))
            if a in by_id and b in by_id: uf.union(a,b)
    groups = defaultdict(list)
    for claim in claims: groups[uf.find(claim.claim_id)].append(claim)
    clusters = [
        tuple(sorted(group, key=lambda c:(-c.authority_rank,c.claim_id)))
        for _, group in sorted(groups.items())
    ]
    clusters.sort(key=lambda g: tuple(c.claim_id for c in g))
    return tuple(clusters)

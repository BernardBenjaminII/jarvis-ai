from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ProbeDefinition:
    probe_id: str
    query: str
    expectation: str
    domain: str
    rationale: str

def canonical_runtime_probes():
    return (
        ProbeDefinition("KNOWN-SHA256","SHA-256","known","cybersecurity","Canonical technical query."),
        ProbeDefinition("KNOWN-SQLITE","SQLite","known","programming","JARVIS uses SQLite."),
        ProbeDefinition("KNOWN-FTS","full text search","known","retrieval","FTS should exist in the corpus."),
        ProbeDefinition("KNOWN-C","professional C programming","known","programming","Known catalog title."),
        ProbeDefinition("KNOWN-COMPUTER-ARCH","computer architecture","known","computer_science","Intended corpus domain."),
        ProbeDefinition("KNOWN-EXECUTIVE-DIRECTOR","Executive Director","known","jarvis","JARVIS source should contain it."),
        ProbeDefinition("POSSIBLE-ANCA","ANCA vasculitis","possible","medical","May or may not be assimilated."),
        ProbeDefinition("GAP-QUANTUM-BANANA","Quantum Banana Warp Core Mk XII","unknown","fabricated","Gap control."),
    )

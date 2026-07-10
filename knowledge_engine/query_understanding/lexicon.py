"""Deterministic lexicons used by Query Understanding."""

from __future__ import annotations


STOPWORDS = frozenset(
    {
        "a",
        "about",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "can",
        "could",
        "do",
        "does",
        "for",
        "from",
        "give",
        "how",
        "i",
        "in",
        "into",
        "is",
        "it",
        "me",
        "my",
        "of",
        "on",
        "or",
        "please",
        "show",
        "tell",
        "that",
        "the",
        "their",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "would",
        "you",
    }
)


TASK_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "compare",
        (
            "compare",
            "difference between",
            "versus",
            " vs ",
            "better than",
        ),
    ),
    (
        "how_to",
        (
            "how do i",
            "how to",
            "steps to",
            "instructions",
            "procedure",
        ),
    ),
    (
        "explain",
        (
            "explain",
            "how does",
            "how do",
            "why does",
            "why is",
            "describe",
        ),
    ),
    (
        "define",
        (
            "what is",
            "what are",
            "define",
            "meaning of",
        ),
    ),
    (
        "list",
        (
            "list",
            "show me",
            "give me",
            "which are",
        ),
    ),
    (
        "locate",
        (
            "find",
            "search",
            "look up",
            "locate",
            "where is",
        ),
    ),
)


DOMAIN_TERMS: dict[str, frozenset[str]] = {
    "databases": frozenset(
        {
            "database",
            "databases",
            "sql",
            "sqlite",
            "postgres",
            "postgresql",
            "mysql",
            "oracle",
            "index",
            "indexes",
            "query",
            "transaction",
            "schema",
        }
    ),
    "information_retrieval": frozenset(
        {
            "retrieval",
            "embedding",
            "embeddings",
            "vector",
            "semantic",
            "ranking",
            "ranker",
            "search",
            "bm25",
            "similarity",
        }
    ),
    "programming": frozenset(
        {
            "python",
            "java",
            "javascript",
            "c++",
            "rust",
            "code",
            "function",
            "class",
            "compiler",
            "programming",
            "algorithm",
        }
    ),
    "cybersecurity": frozenset(
        {
            "cybersecurity",
            "security",
            "vulnerability",
            "network",
            "recon",
            "penetration",
            "nmap",
            "kali",
            "firewall",
        }
    ),
    "aviation": frozenset(
        {
            "aviation",
            "aircraft",
            "helicopter",
            "blackhawk",
            "uh-60",
            "hydraulic",
            "rotor",
            "maintenance",
        }
    ),
    "artificial_intelligence": frozenset(
        {
            "ai",
            "llm",
            "model",
            "agent",
            "agents",
            "machine learning",
            "neural",
            "inference",
            "ollama",
        }
    ),
    "operating_systems": frozenset(
        {
            "linux",
            "ubuntu",
            "windows",
            "macos",
            "kernel",
            "filesystem",
            "process",
            "systemd",
        }
    ),
}


SPECIALISTS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "databases": ("database",),
    "information_retrieval": ("search_engine",),
    "programming": ("software_engineering",),
    "cybersecurity": ("cybersecurity",),
    "aviation": ("aviation_maintenance",),
    "artificial_intelligence": ("artificial_intelligence",),
    "operating_systems": ("systems_engineering",),
}


DESIRED_OUTPUT_BY_TASK: dict[str, str] = {
    "compare": "comparison",
    "how_to": "step_by_step_instructions",
    "explain": "technical_explanation",
    "define": "definition",
    "list": "structured_list",
    "locate": "search_results",
    "research": "evidence_summary",
}

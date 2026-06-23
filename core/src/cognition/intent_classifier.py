# core/src/cognition/intent_classifier.py

from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class IntentResult:
    intent: str
    task_type: str
    confidence: float
    scores: Dict[str, int]
    matched_keywords: Dict[str, List[str]]

INTENT_PRIORITY = [
    "coding",
    "recon",
    "system_admin",
    "planning",
    "writing",
    "research",
    "assistant",
]

INTENT_KEYWORDS = {
    "coding": [
        "code", "script", "python", "java", "javascript", "sql",
        "debug", "bug", "error", "function", "class", "api",
        "fastapi", "compile", "exception", "traceback", "git",
        "github", "repository", "repo",
    ],
    "system_admin": [
        "windows", "linux", "ubuntu", "kali", "powershell", "bash",
        "terminal", "service", "install", "configure", "path",
        "venv", "virtual environment", "docker", "ollama", "mount",
        "partition", "drive", "permissions", "ssh", "systemctl",
    ],
    "recon": [
        "scan", "nmap", "subdomain", "recon", "enumerate",
        "ports", "vulnerability", "vulnerabilities", "httpx",
        "katana", "nuclei", "amass", "subfinder", "network map",
    ],
    "writing": [
        "write", "rewrite", "draft", "resume", "cv", "cover letter",
        "essay", "article", "email", "bio", "paragraph", "edit",
        "proofread", "summarize",
    ],
    "planning": [
        "plan", "roadmap", "steps", "timeline", "strategy",
        "organize", "schedule", "prioritize", "workflow",
        "next step", "path forward", "route forward",
    ],
    "research": [
        "find", "search", "compare", "recommend", "best",
        "what is", "explain", "deep dive", "overview", "learn",
        "research", "look up",
    ],
    "assistant": [
        "hello", "hi", "hey", "thanks", "thank you", "who are you",
        "help me", "can you", "please",
    ],
}


TASK_TYPE_KEYWORDS = {
    "generate": [
        "create", "make", "write", "generate", "build", "draft",
    ],
    "debug": [
        "debug", "fix", "error", "bug", "traceback", "not working",
        "fails", "failed", "broken",
    ],
    "explain": [
        "explain", "what is", "why", "how does", "teach me",
    ],
    "plan": [
        "plan", "roadmap", "steps", "strategy", "timeline",
    ],
    "retrieve": [
        "find", "search", "look up", "show me", "get",
    ],
    "execute": [
        "run", "start", "launch", "install", "configure", "scan",
    ],
}


def _score_keywords(text: str, keywords: List[str]) -> tuple[int, List[str]]:
    import re

    matches = []

    for keyword in keywords:

        pattern = r"\b" + re.escape(keyword) + r"\b"

        if re.search(pattern, text):
            matches.append(keyword)

    return len(matches), matches

def classify_task_type(text: str) -> str:
    text = text.lower()

    best_task = "general"
    best_score = 0

    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        score, _ = _score_keywords(text, keywords)

        if score > best_score:
            best_task = task_type
            best_score = score

    return best_task


def classify_intent(user_input: str) -> dict:
    text = user_input.lower().strip()

    scores = {}
    matched_keywords = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        score, matches = _score_keywords(text, keywords)
        scores[intent] = score
        matched_keywords[intent] = matches
        

    best_score = max(scores.values())

    candidates = [
        intent
        for intent, score in scores.items()
        if score == best_score
    ]

    best_intent = "assistant"

    for intent in INTENT_PRIORITY:
        if intent in candidates:
            best_intent = intent
            break
            
    if best_score == 0:
        best_intent = "assistant"
        confidence = 0.50
    else:
        confidence = min(0.95, 0.55 + best_score * 0.10)

    result = IntentResult(
        intent=best_intent,
        task_type=classify_task_type(text),
        confidence=confidence,
        scores=scores,
        matched_keywords=matched_keywords,
    )

    return asdict(result)


def classify(user_input: str) -> dict:
    """
    Backward-compatible alias.
    """
    return classify_intent(user_input)


if __name__ == "__main__":
    tests = [
        "hi bud",
        "write me a python script to scan my network",
        "help me fix this powershell error",
        "plan my next steps for the JARVIS project",
        "write a resume bullet for my aviation experience",
        "explain how ollama works", "fix my powershell script",
        "why is ollama failing", "scan my network", 
        "write a cover letter", "find scholarships",
        "compare mistral and qwen",
    ]

    for test in tests:
        print(test)
        print(classify_intent(test))
        print()
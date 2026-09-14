"""Conservative routing of non-retrieval requests at the conversation boundary.

Unknown/mixed requests retain the normal knowledge route. This module never
interprets request text as shell code or an instruction to execute tools.
"""
from __future__ import annotations
import re


def normalize(text):
    return " ".join(text.strip().strip('"\'“”‘’').split()).strip('"\'“”‘’').lower()


def request_route(text):
    q = normalize(text).rstrip('.?!')
    runtime_patterns = (
        r"(?:which|what) (?:platform|operating system|os|environment|operational stance|stance|role)(?: and (?:operational )?(?:stance|role))? (?:are you (?:using|running)|do you use)",
        r"what (?:platform|operating system|os|environment) are you running on",
        r"what (?:is|are) your (?:current )?(?:platform|operational stance|stance|role)(?: and (?:operational )?(?:stance|role))?",
        r"(?:show|tell me) your (?:current )?(?:platform|runtime status|operational stance|stance)",
    )
    if any(re.fullmatch(pattern,q) for pattern in runtime_patterns):
        return 'runtime'
    # Evidence-bearing drafts must keep retrieval, even if they begin "write".
    factual = re.search(
        r"\b(?:sources?|citations?|cite|facts?|factual|statistics?|latest|current|research|"
        r"catalog|documents?|pdf|according|based on|summari[sz]e|quote|medical|legal|"
        r"diagnosis|investment|vulnerabilit\w*|cve|scan|run|execute|commands?|"
        r"script|code|report|explain|prove)\b|https?://", q)
    if not factual and not re.search(r'[;?]|\b(?:then|also)\b', q):
        if re.fullmatch(r'(?:hello|hi|hey|thanks|thank you)(?: jarvis)?',q):
            return 'social'
        # Restrict unconstrained generation to recognizably creative artifacts.
        if re.match(r'(?:(?:please|can you|could you)\s+)?(?:write|draft|compose|create|make|tell me)\b',q):
            if re.search(r'\b(?:birthday|anniversary|congratulations|condolence|thank.you|fictional|fiction|poem|poetry|joke|bedtime story)\b',q):
                return 'creative'
    # A question about the command, not a request for measurements or execution.
    if (re.match(r'(?:what|which) command\b|how (?:can|do) i (?:check|show|see)\b',q)
        and re.search(r'\b(?:disk space|disk usage|filesystem space|file system space)\b',q)
        and not re.search(r'[;?]|\b(?:and|then|also|run|execute|delete|remove|windows|macos|remote|server)\b',q)):
        return 'disk_command'
    return 'knowledge'


def runtime_answer(snapshot):
    info = snapshot.get('platform', {})
    label = info.get('distribution') or snapshot['environment']
    version = info.get('version') or ''
    source = 'automatically from the platform' if snapshot.get('stance_source') == 'platform' else 'from an explicit override'
    return (
        f"I’m running on {label.title()} {version} ({info.get('architecture', 'unknown architecture')}). ".replace('  ', ' ')
        + f"My operational stance is {snapshot['stance']}, selected {source}. "
        + f"My configured role is {snapshot.get('role', 'unspecified')}. "
        + "This describes the Jarvis server, rather than the device displaying the chat. "
        + "I can still help with other subjects."
    )

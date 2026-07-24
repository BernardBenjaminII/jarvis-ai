"""Canonical capability routing for JARVIS Convergence C-3."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.executive.registry import DirectorRegistry


@dataclass(frozen=True, slots=True)
class CapabilityProfile:
    name: str
    keywords: tuple[str, ...]
    capabilities: tuple[str, ...]
    action: str
    title: str
    priority: int = 100


@dataclass(frozen=True, slots=True)
class RoutedWork:
    profile: str
    title: str
    action: str
    director: str
    capabilities: tuple[str, ...]
    matched_keywords: tuple[str, ...]
    evidence: dict

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "title": self.title,
            "action": self.action,
            "director": self.director,
            "capabilities": list(self.capabilities),
            "matched_keywords": list(self.matched_keywords),
            "evidence": dict(self.evidence),
        }


DEFAULT_CAPABILITY_PROFILES: tuple[CapabilityProfile, ...] = (
    CapabilityProfile("knowledge", ("knowledge","research","find","search","explain","summarize","document","book","catalog","source","evidence"), ("knowledge_search","knowledge_retrieval"), "search", "Gather relevant knowledge", 10),
    CapabilityProfile("system", ("linux","ubuntu","windows","macos","kali","system","computer","diagnose","repair","install","runtime","server"), ("system_assessment",), "assess", "Assess system requirements", 20),
    CapabilityProfile("planning", ("plan","roadmap","priority","schedule","milestone","strategy","objective","mission"), ("general_reasoning",), "reason", "Develop an execution plan", 30),
    CapabilityProfile("engineering", ("code","program","python","api","debug","test","build","implement","refactor","architecture"), ("general_reasoning",), "reason", "Develop an engineering solution", 40),
)


class CapabilityRouter:
    """Translate an objective and routing hints into deterministic work assignments."""

    def __init__(self, registry: DirectorRegistry, profiles: Iterable[CapabilityProfile] = DEFAULT_CAPABILITY_PROFILES) -> None:
        self.registry = registry
        self.profiles = tuple(sorted(profiles, key=lambda item: (item.priority, item.name)))

    def route(self, objective: str, *, hints: Iterable[str] = ()) -> tuple[RoutedWork, ...]:
        normalized = objective.casefold()
        hint_set = {str(item).strip().casefold() for item in hints if str(item).strip()}
        routed: list[RoutedWork] = []
        seen: set[tuple[str, str]] = set()
        for profile in self.profiles:
            matched = tuple(sorted({word for word in profile.keywords if word in normalized}))
            hinted = profile.name.casefold() in hint_set or bool(hint_set & set(profile.capabilities))
            if not matched and not hinted:
                continue
            decision = self.registry.select(profile.capabilities)
            key = (decision.selected_director, profile.action)
            if key in seen:
                continue
            seen.add(key)
            evidence = decision.to_dict()
            evidence.update({"profile": profile.name, "matched_keywords": list(matched), "routing_hints": sorted(hint_set), "router": "convergence_c3"})
            routed.append(RoutedWork(profile.name, profile.title, profile.action, decision.selected_director, profile.capabilities, matched, evidence))
        if not routed:
            decision = self.registry.select(("general_reasoning",), fallback="executive")
            evidence = decision.to_dict(); evidence.update({"profile":"general","matched_keywords":[],"routing_hints":sorted(hint_set),"router":"convergence_c3"})
            routed.append(RoutedWork("general","Develop a general solution","reason",decision.selected_director,("general_reasoning",),(),evidence))
        return tuple(routed)

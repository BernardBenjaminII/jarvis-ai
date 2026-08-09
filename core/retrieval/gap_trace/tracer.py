from __future__ import annotations

from core.executive.director_dispatch import resolve_director_dispatch
import hashlib, inspect, json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

@dataclass(frozen=True, slots=True)
class Stage:
    ordinal: int
    stage: str
    function: str
    file: str
    line: int | None
    gap_present: bool
    gap_count: int
    status: str | None
    recommended_actions: tuple[str, ...]
    object_type: str | None
    serialized: dict[str, Any]

    def to_dict(self): return asdict(self)

def to_map(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping): return dict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        if isinstance(result, Mapping): return dict(result)
    if is_dataclass(value):
        result = asdict(value)
        if isinstance(result, Mapping): return dict(result)
    return {}

def safe(value: Any) -> Any:
    if value is None or isinstance(value, (str,int,float,bool)): return value
    if isinstance(value, Mapping): return {str(k):safe(v) for k,v in value.items()}
    if isinstance(value, (list,tuple,set)): return [safe(v) for v in value]
    return to_map(value) or repr(value)

def extract_gap_state(value: Any) -> dict[str, Any]:
    data = to_map(value)
    gap_items = []
    gaps = data.get("gaps")
    if isinstance(gaps, (list,tuple)): gap_items.extend(gaps)
    if data.get("gap"): gap_items.append(data["gap"])
    objectives = data.get("objectives")
    if isinstance(objectives, (list,tuple)):
        for objective in objectives:
            mapped = to_map(objective)
            if mapped.get("gap"): gap_items.append(mapped["gap"])
    actions = []
    for item in gap_items:
        action = to_map(item).get("recommended_action")
        if action: actions.append(str(action))
    status = data.get("status")
    if status is None and hasattr(value, "status"):
        try: status = getattr(value, "status")
        except Exception: status = None
    return {
        "gap_present": bool(gap_items),
        "gap_count": len(gap_items),
        "status": None if status is None else str(status),
        "recommended_actions": tuple(actions),
        "serialized": safe(data),
    }

class KnowledgeGapPropagationTracer:
    def __init__(self, repository_root: Path, catalog_database: Path | None):
        self.root = repository_root.resolve()
        self.catalog = catalog_database.resolve() if catalog_database else None
        self.stages: list[Stage] = []
        self.ordinal = 0

    def _record(self, stage, fn, value):
        state = extract_gap_state(value)
        self.ordinal += 1
        try: file = inspect.getsourcefile(fn) or "<unknown>"
        except Exception: file = "<unknown>"
        try: line = inspect.getsourcelines(fn)[1]
        except Exception: line = None
        self.stages.append(Stage(
            self.ordinal, stage,
            getattr(fn, "__qualname__", getattr(fn, "__name__", repr(fn))),
            file, line,
            bool(state["gap_present"]), int(state["gap_count"]),
            state["status"], tuple(state["recommended_actions"]),
            None if value is None else f"{type(value).__module__}.{type(value).__name__}",
            safe(state["serialized"]),
        ))

    def _record_prompt(self, prompt: str):
        self.ordinal += 1
        present = "Knowledge gaps:" in prompt or "No catalog evidence was retrieved." in prompt
        actions = tuple(
            line.strip("- ").strip() for line in prompt.splitlines()
            if "Queue targeted acquisition" in line or "Acquire authoritative sources" in line
        )
        self.stages.append(Stage(
            self.ordinal, "synthesis.prompt", "deterministic_synthesis",
            __file__, None, present,
            prompt.count("Knowledge gaps:") + prompt.count("No catalog evidence was retrieved."),
            "gap" if "Knowledge gaps:" in prompt else None,
            actions, "str", {"prompt": prompt},
        ))

    def run(self, query="internal architecture of the Quantum Banana Warp Core Mk XII"):
        from core.src.routes.api import conversation_service

        orchestrator = conversation_service.orchestrator
        grounding = orchestrator.grounding_service
        awareness = orchestrator.awareness_service
        director = orchestrator.director

        originals = []
        def patch(owner, name, replacement):
            originals.append((owner, name, getattr(owner, name)))
            setattr(owner, name, replacement)

        original_ground = grounding.ground
        original_assess = awareness.assess
        resolved_director = resolve_director_dispatch(
            director,
            preferred='submit',
        )
        original_execute = resolved_director.callable
        original_synthesis = orchestrator.synthesis_handler
        capture = {"query": query, "prompt": "", "response": None, "exception": None}

        def traced_ground(context):
            result = original_ground(context)
            self._record("grounding.result", original_ground, result)
            return result

        def traced_assess(value):
            self._record("awareness.input", original_assess, value)
            result = original_assess(value)
            self._record("awareness.output", original_assess, result)
            return result

        def traced_execute(*args, **kwargs):
            self._record("director.input", original_execute, args[0] if args else kwargs)
            result = original_execute(*args, **kwargs)
            self._record("director.output", original_execute, result)
            return result

        def deterministic_synthesis(*args, **kwargs):
            prompt = next((x for x in args if isinstance(x, str)), "")
            if not prompt:
                prompt = next((x for x in kwargs.values() if isinstance(x, str)), "")
            capture["prompt"] = prompt
            self._record_prompt(prompt)
            return "CERTIFICATION TRACE: prompt captured; no external model invoked."

        patch(grounding, "ground", traced_ground)
        patch(awareness, "assess", traced_assess)
        patch(
            director,
            resolved_director.method_name,
            traced_execute,
        )
        patch(orchestrator, "synthesis_handler", deterministic_synthesis)

        try:
            response = conversation_service.ask(
                query,
                mode="full",
                metadata={"certification":"genesis_ix_a4_3b"},
            )
            capture["response"] = safe(response)
            self._record("conversation.response", conversation_service.ask, response)
        except Exception as exc:
            capture["exception"] = f"{type(exc).__name__}: {exc}"
        finally:
            for owner, name, original in reversed(originals):
                setattr(owner, name, original)

        verdict = self._verdict()
        return {
            "schema_version":"genesis_ix_a4_3b_v1",
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "repository_root":str(self.root),
            "catalog_database":str(self.catalog) if self.catalog else None,
            "query":query,
            "stages":[x.to_dict() for x in self.stages],
            "capture":capture,
            "verdict":verdict,
            "source_locations":self._source_locations(),
        }

    def _verdict(self):
        if not self.stages:
            return {"classification":"CONFIGURATION_DEFECT","first_gap_stage":None,
                    "loss_stage":None,"reason":"No stages captured.","blocking":True}
        first = next((x for x in self.stages if x.gap_present), None)
        if first is None:
            grounding = next((x for x in self.stages if x.stage=="grounding.result"), None)
            if grounding and grounding.status and grounding.status.casefold() in {"grounded","partial"}:
                return {"classification":"DATA_DEFECT","first_gap_stage":None,"loss_stage":None,
                        "reason":f"Unknown query was classified as {grounding.status!r}; evidence prevented gap creation.",
                        "blocking":False}
            return {"classification":"RUNTIME_DEFECT","first_gap_stage":None,"loss_stage":"grounding.result",
                    "reason":"Grounding did not create a KnowledgeGap.","blocking":True}
        seen = False
        previous = None
        for stage in self.stages:
            if stage.gap_present: seen = True
            elif seen:
                return {"classification":"RUNTIME_DEFECT","first_gap_stage":first.stage,
                        "loss_stage":stage.stage,"loss_function":stage.function,
                        "loss_file":stage.file,"loss_line":stage.line,
                        "reason":f"Gap present at {previous.stage if previous else first.stage} and absent at {stage.stage}.",
                        "blocking":True}
            previous = stage
        prompt = next((x for x in self.stages if x.stage=="synthesis.prompt"), None)
        if prompt and prompt.gap_present:
            return {"classification":"CERTIFICATION_DEFECT","first_gap_stage":first.stage,
                    "loss_stage":None,"reason":"Gap survived through synthesis prompt; IX-A4.3 assertion is outdated.",
                    "blocking":False}
        return {"classification":"RUNTIME_DEFECT","first_gap_stage":first.stage,
                "loss_stage":"synthesis.prompt","reason":"Gap existed but did not reach synthesis prompt.",
                "blocking":True}

    def _source_locations(self):
        targets = {
            "grounding":self.root/"core/conversation/grounding.py",
            "awareness":self.root/"core/knowledge_awareness/service.py",
            "orchestrator":self.root/"core/conversation/orchestrator.py",
            "service":self.root/"core/conversation/service.py",
        }
        result = {}
        for name, path in targets.items():
            if not path.is_file():
                result[name] = {"path":str(path),"exists":False}
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            matches = [
                {"line":i,"text":line.strip()} for i,line in enumerate(lines,1)
                if any(token in line for token in (
                    "KnowledgeGap","gap","gaps","synthesis_input",
                    "recommended_action","grounding","knowledge_state"
                ))
            ]
            result[name] = {
                "path":str(path),"exists":True,
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "matches":matches[:250],
            }
        return result

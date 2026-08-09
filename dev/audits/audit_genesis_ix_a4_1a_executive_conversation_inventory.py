from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EXCLUDED_DIRS = {
    ".git", ".migration_backups", "__pycache__", ".pytest_cache",
    ".mypy_cache", "node_modules", "dist", "build", "htmlcov",
    ".venv", "venv", "artifacts", "architecture_contract_20260724_091739",
}

TERMS = (
    "executive", "conversation", "director", "orchestrator", "compiler",
    "repository", "session", "trace", "request", "response", "grounding",
    "awareness", "planner", "dispatcher", "controller", "coordinator",
    "supervisor",
)

CANONICAL_HINTS = {
    "ExecutiveConversationService",
    "ExecutiveConversationOrchestrator",
    "ExecutiveDirector",
    "ExecutiveRequestContext",
    "ExecutiveConversationResponse",
    "ConversationTraceEvent",
    "CatalogGroundingService",
    "ExecutiveKnowledgeAwarenessService",
}


@dataclass
class SymbolRecord:
    path: str
    line: int
    kind: str
    name: str
    qualified_name: str
    bases: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)
    returns: str | None = None
    terms: list[str] = field(default_factory=list)


@dataclass
class ImportEdge:
    source: str
    target: str
    line: int
    names: list[str] = field(default_factory=list)


@dataclass
class CallEdge:
    source: str
    target: str
    path: str
    line: int


@dataclass
class RouteRecord:
    path: str
    line: int
    method: str
    route: str
    function: str
    response_model: str | None = None


@dataclass
class UiClientRecord:
    path: str
    line: int
    endpoint: str
    method: str
    transport: str


@dataclass
class DuplicateGroup:
    category: str
    members: list[str]
    rationale: str


@dataclass
class CanonicalizationRecord:
    component: str
    classification: str
    rationale: str
    evidence: list[str]


def iter_source_files(root: Path, suffixes: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in suffixes:
            yield path


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def annotation(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def terms_for(text: str) -> list[str]:
    lowered = text.casefold()
    return sorted({term for term in TERMS if term in lowered})


def symbol_inventory(root: Path) -> list[SymbolRecord]:
    records: list[SymbolRecord] = []

    for path in iter_source_files(root, {".py"}):
        try:
            tree = ast.parse(read_source(path))
        except Exception:
            continue

        stack: list[str] = []

        class Visitor(ast.NodeVisitor):
            def visit_ClassDef(self, node: ast.ClassDef) -> Any:
                qualified = ".".join([*stack, node.name])
                matched = terms_for(
                    " ".join(
                        [
                            node.name,
                            ast.get_docstring(node) or "",
                            *(annotation(base) or "" for base in node.bases),
                        ]
                    )
                )
                if matched:
                    records.append(
                        SymbolRecord(
                            path=str(path.relative_to(root)),
                            line=node.lineno,
                            kind="class",
                            name=node.name,
                            qualified_name=qualified,
                            bases=[annotation(base) or "<unknown>" for base in node.bases],
                            terms=matched,
                        )
                    )
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
                qualified = ".".join([*stack, node.name])
                parameters = [
                    item.arg
                    for item in [
                        *node.args.posonlyargs,
                        *node.args.args,
                        *node.args.kwonlyargs,
                    ]
                    if item.arg != "self"
                ]
                matched = terms_for(
                    " ".join(
                        [
                            node.name,
                            ast.get_docstring(node) or "",
                            " ".join(parameters),
                            annotation(node.returns) or "",
                            " ".join(stack),
                        ]
                    )
                )
                if matched:
                    records.append(
                        SymbolRecord(
                            path=str(path.relative_to(root)),
                            line=node.lineno,
                            kind="function",
                            name=node.name,
                            qualified_name=qualified,
                            parameters=parameters,
                            returns=annotation(node.returns),
                            terms=matched,
                        )
                    )
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

        Visitor().visit(tree)

    return sorted(records, key=lambda item: (item.path, item.line, item.name))


def import_inventory(root: Path) -> list[ImportEdge]:
    edges: list[ImportEdge] = []

    for path in iter_source_files(root, {".py"}):
        try:
            tree = ast.parse(read_source(path))
        except Exception:
            continue
        relative = str(path.relative_to(root))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if terms_for(alias.name):
                        edges.append(
                            ImportEdge(
                                source=relative,
                                target=alias.name,
                                line=node.lineno,
                                names=[alias.asname or alias.name],
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                if terms_for(" ".join([module, *names])):
                    edges.append(
                        ImportEdge(
                            source=relative,
                            target=module,
                            line=node.lineno,
                            names=names,
                        )
                    )

    return sorted(edges, key=lambda item: (item.source, item.line, item.target))


def call_inventory(root: Path) -> list[CallEdge]:
    edges: list[CallEdge] = []

    for path in iter_source_files(root, {".py"}):
        try:
            tree = ast.parse(read_source(path))
        except Exception:
            continue
        relative = str(path.relative_to(root))
        stack: list[str] = []

        class Visitor(ast.NodeVisitor):
            def visit_ClassDef(self, node: ast.ClassDef) -> Any:
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Call(self, node: ast.Call) -> Any:
                try:
                    target = ast.unparse(node.func)
                except Exception:
                    target = "<unknown>"
                if terms_for(target):
                    edges.append(
                        CallEdge(
                            source=".".join(stack) or "<module>",
                            target=target,
                            path=relative,
                            line=node.lineno,
                        )
                    )
                self.generic_visit(node)

        Visitor().visit(tree)

    return sorted(edges, key=lambda item: (item.path, item.line, item.source))


ROUTE_RE = re.compile(
    r'''@router\.(get|post|put|patch|delete|websocket)\(\s*["']([^"']+)["']'''
)
DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")
RESPONSE_RE = re.compile(r"response_model\s*=\s*([^,\)]+)")


def route_inventory(root: Path) -> list[RouteRecord]:
    records: list[RouteRecord] = []
    route_root = root / "core/src/routes"
    if not route_root.exists():
        return records

    for path in route_root.rglob("*.py"):
        lines = read_source(path).splitlines()
        for index, line in enumerate(lines):
            match = ROUTE_RE.search(line)
            if not match:
                continue

            function = "<unknown>"
            block = line
            for probe in lines[index + 1:index + 12]:
                block += " " + probe
                found = DEF_RE.match(probe)
                if found:
                    function = found.group(1)
                    break

            response = RESPONSE_RE.search(block)
            records.append(
                RouteRecord(
                    path=str(path.relative_to(root)),
                    line=index + 1,
                    method=match.group(1).upper(),
                    route=match.group(2),
                    function=function,
                    response_model=response.group(1).strip() if response else None,
                )
            )

    return sorted(records, key=lambda item: (item.route, item.method, item.path))


UI_CALL_RE = re.compile(
    r'''(?P<call>fetch|postJson|getJson|request|WebSocket)\s*\(\s*["'](?P<endpoint>/[^"']+)["']'''
)


def ui_inventory(root: Path) -> list[UiClientRecord]:
    records: list[UiClientRecord] = []
    ui_root = root / "core/src/static/mission_control"
    if not ui_root.exists():
        return records

    for path in iter_source_files(ui_root, {".js", ".html"}):
        for number, line in enumerate(read_source(path).splitlines(), 1):
            for match in UI_CALL_RE.finditer(line):
                call = match.group("call")
                records.append(
                    UiClientRecord(
                        path=str(path.relative_to(root)),
                        line=number,
                        endpoint=match.group("endpoint"),
                        method="POST" if call == "postJson" else "GET",
                        transport="websocket" if call == "WebSocket" else "http",
                    )
                )

    return sorted(records, key=lambda item: (item.endpoint, item.path, item.line))


def live_composition(root: Path) -> dict[str, Any]:
    probe = (
        "import inspect, json\n"
        "result={}\n"
        "try:\n"
        " from core.src.routes.api import conversation_service\n"
        " result['conversation_service']={'type':type(conversation_service).__name__,'module':type(conversation_service).__module__}\n"
        " for a in ('compiler','repository','orchestrator','answer_handler'):\n"
        "  v=getattr(conversation_service,a,None)\n"
        "  result['conversation_service'][a]=None if v is None else {'type':type(v).__name__,'module':type(v).__module__}\n"
        " o=getattr(conversation_service,'orchestrator',None)\n"
        " if o is not None:\n"
        "  result['orchestrator']={'type':type(o).__name__,'module':type(o).__module__}\n"
        "  for a in ('director','grounding_service','awareness_service','observability_service','synthesis_handler'):\n"
        "   v=getattr(o,a,None)\n"
        "   result['orchestrator'][a]=None if v is None else {'type':type(v).__name__,'module':type(v).__module__}\n"
        " result['ask_signature']=str(inspect.signature(conversation_service.ask))\n"
        "except Exception as e:\n"
        " result['error']=type(e).__name__+': '+str(e)\n"
        "print(json.dumps(result))\n"
    )
    completed = subprocess.run(
        [os.environ.get("PYTHON_BIN", "python"), "-c", probe],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=45,
    )
    lines = [
        line for line in completed.stdout.splitlines()
        if line.strip().startswith("{")
    ]
    if not lines:
        return {
            "error": completed.stderr.strip()
            or completed.stdout.strip()
            or "composition probe produced no JSON"
        }
    try:
        return json.loads(lines[-1])
    except Exception:
        return {"error": "composition probe returned invalid JSON"}


def classify_duplicates(symbols: list[SymbolRecord]) -> list[DuplicateGroup]:
    categories = {
        "conversation services": ("ConversationService",),
        "orchestrators": ("Orchestrator",),
        "compilers": ("Compiler",),
        "repositories": ("Repository",),
        "request models": ("Request", "RequestContext"),
        "response models": ("Response",),
        "trace models": ("Trace", "TraceEvent"),
        "session models": ("Session",),
    }
    classes = [item for item in symbols if item.kind == "class"]
    groups: list[DuplicateGroup] = []

    for category, hints in categories.items():
        members = sorted(
            {
                f"{item.name} ({item.path}:{item.line})"
                for item in classes
                if any(hint.casefold() in item.name.casefold() for hint in hints)
            }
        )
        if len(members) > 1:
            groups.append(
                DuplicateGroup(
                    category=category,
                    members=members,
                    rationale=(
                        "Multiple similarly named classes exist. Runtime wiring "
                        "and consumer analysis must determine whether these are "
                        "canonical objects, adapters, compatibility layers, or duplicates."
                    ),
                )
            )

    return groups


def live_types(live: dict[str, Any]) -> set[str]:
    result: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("type"), str):
                result.add(value["type"])
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(live)
    return result


def canonicalization(
    symbols: list[SymbolRecord],
    live: dict[str, Any],
    duplicates: list[DuplicateGroup],
) -> list[CanonicalizationRecord]:
    active = live_types(live)
    duplicate_names = {
        member.split(" (", 1)[0]
        for group in duplicates
        for member in group.members
    }
    records: list[CanonicalizationRecord] = []
    seen: set[str] = set()

    for item in symbols:
        if item.kind != "class" or item.name in seen:
            continue
        seen.add(item.name)

        if item.name in active:
            decision = "KEEP"
            rationale = "Active in the live runtime composition."
        elif item.name in CANONICAL_HINTS:
            decision = "KEEP"
            rationale = "Matches an established Executive or Conversation contract."
        elif item.name in duplicate_names:
            decision = "UNKNOWN"
            rationale = "Potential overlap requires consumer and runtime verification."
        elif "adapter" in item.name.casefold():
            decision = "KEEP"
            rationale = "Compatibility adapter; preserve until consumers are migrated."
        elif "legacy" in item.path.casefold() or "compat" in item.path.casefold():
            decision = "MERGE"
            rationale = "Compatibility-oriented source path; consolidation candidate."
        else:
            decision = "UNKNOWN"
            rationale = "Static existence found, but canonical runtime ownership is unproven."

        records.append(
            CanonicalizationRecord(
                component=item.name,
                classification=decision,
                rationale=rationale,
                evidence=[f"{item.path}:{item.line}"],
            )
        )

    return sorted(records, key=lambda item: (item.classification, item.component))


def dependency_graph(
    live: dict[str, Any],
    routes: list[RouteRecord],
    ui: list[UiClientRecord],
) -> str:
    lines = [
        "# Genesis IX-A4.1A — Executive Dependency Graph",
        "",
        "```mermaid",
        "flowchart TD",
        "    UI[Mission Control / Knowledge Workspace]",
        "    API[Conversation API]",
        "    SVC[ExecutiveConversationService]",
        "    COMP[Objective Compiler]",
        "    REPO[Conversation Repository]",
        "    ORCH[ExecutiveConversationOrchestrator]",
        "    GROUND[CatalogGroundingService]",
        "    AWARE[ExecutiveKnowledgeAwarenessService]",
        "    DIR[ExecutiveDirector]",
        "    SYNTH[Synthesis Handler / LLM]",
        "    TRACE[Conversation Trace]",
        "    RESP[ExecutiveConversationResponse]",
        "    UI --> API",
        "    API --> SVC",
        "    SVC --> COMP",
        "    SVC --> REPO",
        "    SVC --> ORCH",
        "    ORCH --> GROUND",
        "    ORCH --> AWARE",
        "    ORCH --> DIR",
        "    ORCH --> SYNTH",
        "    ORCH --> TRACE",
        "    TRACE --> RESP",
        "    RESP --> REPO",
        "    RESP --> UI",
        "```",
        "",
        "## Live composition",
        "",
        "```json",
        json.dumps(live, indent=2, sort_keys=True),
        "```",
        "",
        "## Executive-facing routes",
        "",
    ]
    for item in routes:
        if any(token in item.route for token in (
            "conversation", "ask", "knowledge", "executive", "bridge",
        )):
            lines.append(
                f"- `{item.method} {item.route}` → `{item.function}` "
                f"(`{item.path}:{item.line}`)"
            )
    lines.extend(["", "## Mission Control consumers", ""])
    for item in ui:
        if any(token in item.endpoint for token in (
            "conversation", "knowledge", "executive", "bridge",
        )):
            lines.append(
                f"- `{item.method} {item.endpoint}` "
                f"({item.transport}, `{item.path}:{item.line}`)"
            )
    return "\n".join(lines)


def call_graph(
    routes: list[RouteRecord],
    calls: list[CallEdge],
    live: dict[str, Any],
) -> str:
    lines = [
        "# Genesis IX-A4.1A — Executive Call Graph",
        "",
        "```text",
        "Mission Control / Knowledge Workspace",
        "  ↓",
        "HTTP route",
        "  ↓",
        "ExecutiveConversationService.ask()",
        "  ↓",
        "Objective compiler",
        "  ↓",
        "ExecutiveRequestContext",
        "  ↓",
        "Conversation repository: operator message",
        "  ↓",
        "ExecutiveConversationOrchestrator.execute()",
        "  ↓",
        "Grounding → Knowledge Awareness → Executive Director",
        "  ↓",
        "Synthesis handler",
        "  ↓",
        "ExecutiveConversationResponse + trace",
        "  ↓",
        "Conversation repository: JARVIS message",
        "  ↓",
        "Mission Control projection",
        "```",
        "",
        "## Routes",
        "",
    ]
    for item in routes:
        if any(token in item.route for token in (
            "conversation", "ask", "knowledge", "executive",
        )):
            lines.append(
                f"- `{item.method} {item.route}` → `{item.function}` "
                f"(`{item.path}:{item.line}`)"
            )
    lines.extend(["", "## Static call references", ""])
    for item in calls[:400]:
        lines.append(
            f"- `{item.source}` → `{item.target}` "
            f"(`{item.path}:{item.line}`)"
        )
    lines.extend([
        "", "## Live composition", "", "```json",
        json.dumps(live, indent=2, sort_keys=True), "```",
    ])
    return "\n".join(lines)


def component_matrix(symbols: list[SymbolRecord], live: dict[str, Any]) -> str:
    active = live_types(live)
    lines = [
        "# Genesis IX-A4.1A — Executive Component Matrix",
        "",
        "| Component | Live | Domains | Source |",
        "|---|---|---|---|",
    ]
    rows = {
        (
            item.name,
            "yes" if item.name in active else "no",
            ", ".join(item.terms),
            f"{item.path}:{item.line}",
        )
        for item in symbols
        if item.kind == "class"
    }
    for name, is_live, domains, source in sorted(rows):
        lines.append(f"| `{name}` | {is_live} | {domains} | `{source}` |")
    return "\n".join(lines)


def duplicate_report(groups: list[DuplicateGroup]) -> str:
    lines = [
        "# Genesis IX-A4.1A — Executive Duplicate Report",
        "",
    ]
    if not groups:
        lines.append("No duplicate candidate groups were detected.")
        return "\n".join(lines)

    for group in groups:
        lines.extend([
            f"## {group.category.title()}",
            "",
            group.rationale,
            "",
        ])
        lines.extend(f"- `{member}`" for member in group.members)
        lines.append("")
    return "\n".join(lines)


def main_inventory(report: dict[str, Any]) -> str:
    lines = [
        "# Genesis IX-A4.1A — Executive & Conversation Inventory",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Repository:** `{report['repository_root']}`",
        f"**Fingerprint:** `{report['fingerprint']}`",
        "",
        "## Executive Summary",
        "",
        f"- Executive/conversation symbols: **{len(report['symbols'])}**",
        f"- Import edges: **{len(report['imports'])}**",
        f"- Static call edges: **{len(report['calls'])}**",
        f"- API routes: **{len(report['routes'])}**",
        f"- Mission Control consumers: **{len(report['ui_clients'])}**",
        f"- Duplicate candidate groups: **{len(report['duplicates'])}**",
        "",
        "## Live Runtime Composition",
        "",
        "```json",
        json.dumps(report["live_composition"], indent=2, sort_keys=True),
        "```",
        "",
        "## API Inventory",
        "",
        "| Method | Route | Function | Response model | Source |",
        "|---|---|---|---|---|",
    ]
    for item in report["routes"]:
        lines.append(
            f"| {item['method']} | `{item['route']}` | `{item['function']}` | "
            f"`{item['response_model'] or ''}` | `{item['path']}:{item['line']}` |"
        )

    lines.extend([
        "", "## Mission Control Consumers", "",
        "| Method | Endpoint | Transport | Source |",
        "|---|---|---|---|",
    ])
    for item in report["ui_clients"]:
        lines.append(
            f"| {item['method']} | `{item['endpoint']}` | "
            f"{item['transport']} | `{item['path']}:{item['line']}` |"
        )

    lines.extend([
        "", "## Canonicalization", "",
        "| Component | Decision | Rationale |",
        "|---|---|---|",
    ])
    for item in report["canonicalization"]:
        lines.append(
            f"| `{item['component']}` | **{item['classification']}** | "
            f"{item['rationale']} |"
        )

    lines.extend([
        "", "## Follow-on", "",
        "1. Verify duplicate candidates against actual consumers.",
        "2. Certify one canonical service, orchestrator, compiler, repository, request model, response model, and trace model.",
        "3. Preserve compatibility adapters until every consumer has migrated.",
        "4. Attach IX-A4.1B retrieval inventory to this certified Executive call graph.",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/audits/genesis_ix_a4_1a"),
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output_dir
    if not output.is_absolute():
        output = root / output
    output.mkdir(parents=True, exist_ok=True)

    symbols = symbol_inventory(root)
    imports = import_inventory(root)
    calls = call_inventory(root)
    routes = route_inventory(root)
    ui = ui_inventory(root)
    live = live_composition(root)
    duplicates = classify_duplicates(symbols)
    canonical = canonicalization(symbols, live, duplicates)

    report: dict[str, Any] = {
        "schema_version": "genesis_ix_a4_1a_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(root),
        "symbols": [asdict(item) for item in symbols],
        "imports": [asdict(item) for item in imports],
        "calls": [asdict(item) for item in calls],
        "routes": [asdict(item) for item in routes],
        "ui_clients": [asdict(item) for item in ui],
        "live_composition": live,
        "duplicates": [asdict(item) for item in duplicates],
        "canonicalization": [asdict(item) for item in canonical],
    }
    payload = json.dumps(report, sort_keys=True)
    report["fingerprint"] = hashlib.sha256(payload.encode()).hexdigest()

    outputs = {
        "executive_inventory.md": main_inventory(report),
        "conversation_inventory.md": main_inventory(report),
        "executive_dependency_graph.md": dependency_graph(live, routes, ui),
        "executive_runtime_inventory.json": json.dumps(report, indent=2, sort_keys=True),
        "executive_call_graph.md": call_graph(routes, calls, live),
        "executive_component_matrix.md": component_matrix(symbols, live),
        "executive_duplicate_report.md": duplicate_report(duplicates),
    }

    for name, content in outputs.items():
        (output / name).write_text(content.rstrip() + "\n", encoding="utf-8")

    print("=" * 76)
    print("GENESIS IX-A4.1A — EXECUTIVE & CONVERSATION INVENTORY")
    print("=" * 76)
    print("Symbols      :", len(symbols))
    print("Import edges :", len(imports))
    print("Call edges   :", len(calls))
    print("Routes       :", len(routes))
    print("UI clients   :", len(ui))
    print("Duplicates   :", len(duplicates))
    print("Output       :", output)
    print("Fingerprint  :", report["fingerprint"])
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

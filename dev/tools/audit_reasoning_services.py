#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / 'core/reasoning'
REPORT_ROOT = PROJECT_ROOT / 'docs/architecture/convergence'
JSON_REPORT = REPORT_ROOT / 'genesis_1a2_reasoning_service_audit.json'
MARKDOWN_REPORT = REPORT_ROOT / 'genesis_1a2_reasoning_service_audit.md'
AUDIT_ID = 'GENESIS-I-A2'
AUDIT_VERSION = '1.0.0'
REQUIRED_SERVICE = 'ReasoningEngine'

class AuditError(RuntimeError):
    pass

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()

def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))

def source_text(node: ast.AST | None) -> str:
    if node is None:
        return ''
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__

def parse_module(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        tree = ast.parse(raw.decode('utf-8'), filename=str(path))
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise AuditError(f'Unable to parse {rel(path)}: {exc}') from exc

    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    imports: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = '.' * node.level
            module = node.module or ''
            imports.append(f"{prefix}{module}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                'name': node.name,
                'line': node.lineno,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'return_annotation': source_text(node.returns),
            })
        elif isinstance(node, ast.ClassDef):
            methods = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        'name': child.name,
                        'line': child.lineno,
                        'is_async': isinstance(child, ast.AsyncFunctionDef),
                        'return_annotation': source_text(child.returns),
                    })
            classes.append({
                'name': node.name,
                'line': node.lineno,
                'bases': [source_text(base) for base in node.bases],
                'methods': methods,
            })

    return {
        'module': '.'.join(path.relative_to(PROJECT_ROOT).with_suffix('').parts),
        'path': rel(path),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'classes': classes,
        'functions': functions,
        'imports': sorted(imports),
    }

def build_report() -> dict[str, Any]:
    if not SOURCE_ROOT.is_dir():
        raise AuditError(f'Missing canonical reasoning package: {SOURCE_ROOT}')

    paths = sorted(p for p in SOURCE_ROOT.rglob('*.py') if '__pycache__' not in p.parts)
    if not paths:
        raise AuditError(f'No Python modules found beneath {SOURCE_ROOT}')

    modules = [parse_module(path) for path in paths]
    classes = [
        {'name': cls['name'], 'module': module['module'], 'path': module['path'], 'line': cls['line']}
        for module in modules for cls in module['classes']
    ]
    service_entries = [
        {
            'name': cls['name'],
            'module': module['module'],
            'path': module['path'],
            'line': cls['line'],
            'methods': cls['methods'],
        }
        for module in modules for cls in module['classes']
        if cls['name'] == REQUIRED_SERVICE
    ]

    forbidden_prefixes = ('requests', 'httpx', 'urllib.request', 'socket', 'subprocess')
    forbidden_imports = [
        f"{module['path']}: {name}"
        for module in modules for name in module['imports']
        if name.startswith(forbidden_prefixes)
    ]

    duplicate_map: dict[str, list[str]] = {}
    for item in classes:
        if not item['name'].startswith('_'):
            duplicate_map.setdefault(item['name'], []).append(item['path'])
    duplicates = {name: paths for name, paths in duplicate_map.items() if len(paths) > 1}

    public_methods = []
    async_methods = []
    if service_entries:
        public_methods = [m['name'] for m in service_entries[0]['methods'] if not m['name'].startswith('_')]
        async_methods = [m['name'] for m in service_entries[0]['methods'] if m['is_async']]

    checks = [
        ('I-A2-001', 'Canonical reasoning package exists', SOURCE_ROOT.is_dir(), rel(SOURCE_ROOT)),
        ('I-A2-002', 'Reasoning modules discovered', bool(modules), f'modules={len(modules)}'),
        ('I-A2-003', 'ReasoningEngine service exists', len(service_entries) == 1, f'count={len(service_entries)}'),
        ('I-A2-004', 'ReasoningEngine exposes public execution behavior', bool(public_methods), ', '.join(public_methods) or 'none'),
        ('I-A2-005', 'ReasoningEngine core is synchronous', not async_methods, ', '.join(async_methods) or 'no async methods'),
        ('I-A2-006', 'No direct network or process imports', not forbidden_imports, '; '.join(forbidden_imports) or 'none'),
        ('I-A2-007', 'Public reasoning class names are unique', not duplicates, canonical_json(duplicates) if duplicates else 'unique'),
    ]
    check_records = [
        {'check_id': cid, 'title': title, 'passed': passed, 'status': 'PASS' if passed else 'FAIL', 'detail': detail}
        for cid, title, passed, detail in checks
    ]
    failed = sum(1 for item in check_records if not item['passed'])

    report: dict[str, Any] = {
        'audit_id': AUDIT_ID,
        'audit_version': AUDIT_VERSION,
        'title': 'Reasoning Service Audit',
        'status': 'PASS' if failed == 0 else 'FAIL',
        'purpose': 'Certify the canonical Reasoning Engine service boundary before architecture-baseline synthesis.',
        'source_root': rel(SOURCE_ROOT),
        'required_service': REQUIRED_SERVICE,
        'summary': {
            'module_count': len(modules),
            'class_count': len(classes),
            'service_count': len(service_entries),
            'checks_passed': len(check_records) - failed,
            'checks_failed': failed,
        },
        'services': service_entries,
        'classes': classes,
        'modules': {module['module']: module for module in modules},
        'checks': check_records,
        'architecture_findings': {
            'canonical_service': REQUIRED_SERVICE,
            'service_present': bool(service_entries),
            'deterministic_core_expected': True,
            'direct_retrieval_allowed': False,
            'direct_execution_allowed': False,
            'evolution_policy': 'Wrap the service with lifecycle and governance layers rather than absorbing those concerns into ReasoningEngine.',
        },
    }
    report['audit_fingerprint'] = fingerprint(report)
    return report

def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + '\n'

def render_markdown(report: dict[str, Any]) -> str:
    s = report['summary']
    lines = [
        '# Genesis I-A2 — Reasoning Service Audit', '',
        f"**Audit ID:** `{report['audit_id']}`  ",
        f"**Version:** `{report['audit_version']}`  ",
        f"**Status:** **{report['status']}**  ",
        f"**Fingerprint:** `{report['audit_fingerprint']}`", '',
        '## Purpose', '', report['purpose'], '',
        '## Summary', '',
        '| Measure | Value |', '|---|---:|',
        f"| Modules | {s['module_count']} |",
        f"| Classes | {s['class_count']} |",
        f"| Canonical services | {s['service_count']} |",
        f"| Checks passed | {s['checks_passed']} |",
        f"| Checks failed | {s['checks_failed']} |", '',
        '## Certification Checks', '',
        '| Check | Result | Detail |', '|---|---|---|',
    ]
    for check in report['checks']:
        detail = str(check['detail']).replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| `{check['check_id']}` {check['title']} | **{check['status']}** | {detail} |")
    lines += ['', '## Canonical Service', '']
    for service in report['services']:
        lines += [
            f"### `{service['name']}`", '',
            f"- Module: `{service['module']}`",
            f"- Source: `{service['path']}:{service['line']}`", '',
            '| Method | Async | Return |', '|---|---|---|',
        ]
        for method in service['methods']:
            lines.append(f"| `{method['name']}` | {'Yes' if method['is_async'] else 'No'} | `{method['return_annotation'] or 'unspecified'}` |")
    lines += [
        '', '## Architectural Finding', '',
        'The canonical `ReasoningEngine` remains the deterministic reasoning service. Future lifecycle, governance, provenance, adaptive control, calibration, and learning concerns must wrap this service through explicit extension layers.', '',
        '## Genesis Dependency', '',
        'A passing I-A2 report is required before Genesis I-A4 may synthesize the canonical Reasoning Architecture Baseline.', '',
    ]
    return '\n'.join(lines)

def check_file(path: Path, expected: str) -> bool:
    if not path.is_file():
        print(f'[FAIL] Missing output: {rel(path)}')
        return False
    if path.read_text(encoding='utf-8') != expected:
        print(f'[FAIL] Stale output: {rel(path)}')
        return False
    print(f'[PASS] Current output: {rel(path)}')
    return True

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        report = build_report()
    except (AuditError, OSError, ValueError) as exc:
        print(f'[FAIL] {exc}')
        return 1
    json_text = render_json(report)
    md_text = render_markdown(report)
    if args.check:
        current = check_file(JSON_REPORT, json_text) and check_file(MARKDOWN_REPORT, md_text)
        if report['status'] != 'PASS':
            print('[FAIL] Service audit contains failed checks.')
            return 1
        return 0 if current else 1
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json_text, encoding='utf-8')
    MARKDOWN_REPORT.write_text(md_text, encoding='utf-8')
    print(f'[WRITE] {rel(JSON_REPORT)}')
    print(f'[WRITE] {rel(MARKDOWN_REPORT)}')
    print(f"[INFO] Checks passed={report['summary']['checks_passed']} failed={report['summary']['checks_failed']}")
    print(f"[INFO] Audit fingerprint={report['audit_fingerprint']}")
    if report['status'] != 'PASS':
        for check in report['checks']:
            if not check['passed']:
                print(f"[FAIL] {check['check_id']} {check['title']}: {check['detail']}")
        return 1
    print('[PASS] Genesis I-A2 reasoning service audit')
    return 0

if __name__ == '__main__':
    sys.exit(main())

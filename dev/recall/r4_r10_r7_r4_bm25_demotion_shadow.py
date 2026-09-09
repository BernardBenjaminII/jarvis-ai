from __future__ import annotations
from dev.recall.r4_r10_r7_exact_feature_engine import exact_feature_rows
from dev.recall.r4_r10_r7_isolated_primitives import FILE_NOISE, GENERIC_QUERY_NOISE, query_identity_tokens, title_identity_tokens, title_identity_coverage, r7_exact_feature_vector
import ast
import csv
import hashlib
import importlib.util
import json
import math
import re
import sqlite3
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
PROJECT = Path('/media/abdullah/JARVISDATA/Projects/jarvis-ai')
DB = Path('/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite')
OUTDIR = PROJECT / 'artifacts' / 'genesis_recall'
R7R1 = PROJECT / 'dev' / 'recall' / 'r4_r10_r7_r1_79286_tie_set.py'
R7R3_REPORT = OUTDIR / 'r4_r10_r7_r3_shadow_score_component_attribution.json'
R3 = OUTDIR / 'r3_production_recall_census.tsv'
REPORT = OUTDIR / 'r4_r10_r7_r4_bm25_demotion_shadow.json'
R3_DETAIL = OUTDIR / 'r4_r10_r7_r4_r3_250_recall.tsv'
R6_DETAIL = OUTDIR / 'r4_r10_r7_r4_r6_canaries.tsv'
IDENTITY_DETAIL = OUTDIR / 'r4_r10_r7_r4_identity_canaries.tsv'
SEMANTIC_DETAIL = OUTDIR / 'r4_r10_r7_r4_semantic_controls.tsv'
ADVERSARIAL_DETAIL = OUTDIR / 'r4_r10_r7_r4_adversarial.tsv'
TARGET_DETAIL = OUTDIR / 'r4_r10_r7_r4_target_79286.tsv'
TRACE = OUTDIR / 'r4_r10_r7_r4_trace.txt'
SOURCE_CONTRACT = OUTDIR / 'r4_r10_r7_r4_source_contract.txt'
TARGET_DOCUMENT = 79286
TARGET_QUERY = '2008 11 1 html'
POOL_LIMIT = 12000
sys.path.insert(0, str(PROJECT))
from core.knowledge_catalog.materialization.search import search_runtime_knowledge
r7r3 = json.loads(R7R3_REPORT.read_text(encoding='utf-8'))
if not r7r3.get('diagnostic_certified'):
    raise RuntimeError('R7-R3 diagnostic is not certified')
if r7r3.get('root_cause') != 'BM25_POSITION_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER':
    raise RuntimeError('unexpected R7-R3 root cause')
spec = importlib.util.spec_from_file_location('genesis_r7r1', R7R1)
if spec is None or spec.loader is None:
    raise RuntimeError('unable to load R7-R1 harness')
r7 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = r7
R7_PRIMITIVE_SOURCE = Path('/media/abdullah/JARVISDATA/Projects/jarvis-ai/artifacts/genesis_recall/r4_r10_r7_r4_r1_r2_isolated_r7_primitives.py')
if not R7_PRIMITIVE_SOURCE.is_file():
    raise RuntimeError('isolated R7 primitive source missing')
_r7_namespace = {}
exec(compile(R7_PRIMITIVE_SOURCE.read_text(encoding='utf-8'), str(R7_PRIMITIVE_SOURCE), 'exec'), _r7_namespace)

class _R7PrimitiveNamespace:

    def __init__(self):
        self.IDENTITY_CANARIES = (('cpp', 'C++ Programming', 4), ('effective_c', 'Effective C', 14), ('ai_assisted_python', 'AI assisted Python', 11), ('lane', 'Lane lexicon', 86876))
        self.SEMANTIC_CONTROLS = ('civil defense manual', 'US Army survival manual', 'practical electronics handbook', 'Marx mathematical manuscripts')
r7 = _R7PrimitiveNamespace()
for _name, _value in _r7_namespace.items():
    if _name.startswith('__'):
        continue
    setattr(r7, _name, _value)
WEIGHTS = {'coverage': 0.4, 'rarity_coverage': 0.27, 'title_coverage': 0.23, 'numeric_identity': 0.07}
EXPECTED_PRIMARY_MAX = sum(WEIGHTS.values())
if not math.isclose(EXPECTED_PRIMARY_MAX, 0.97, rel_tol=0.0, abs_tol=1e-15):
    raise RuntimeError('unexpected R7-R4 primary weight sum')

@dataclass(frozen=True)
class ShadowCandidate:
    document_id: int
    chunk_id: int
    title: str
    production_rank: int
    coverage: float
    rarity_coverage: float
    title_coverage: float
    numeric_identity: float
    full_title_identity: float
    bm25_position: float
    r7_score: float
    r7_r4_score: float

def get_value(row: Mapping[str, Any] | Any, key: str, default: Any=None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    try:
        return row[key]
    except Exception:
        return getattr(row, key, default)

def integer(value: Any, default: int=0) -> int:
    try:
        return int(value)
    except Exception:
        return default

def floating(value: Any, default: float=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default

def document_id_of(row: Mapping[str, Any] | Any) -> int:
    for key in ('document_id', 'runtime_document_id', 'doc_id'):
        value = get_value(row, key)
        if value not in (None, ''):
            return integer(value)
    metadata = get_value(row, 'metadata', {})
    if isinstance(metadata, Mapping):
        for key in ('document_id', 'runtime_document_id', 'doc_id'):
            if key in metadata:
                return integer(metadata[key])
    return 0

def chunk_id_of(row: Mapping[str, Any] | Any) -> int:
    for key in ('chunk_id', 'id'):
        value = get_value(row, key)
        if value not in (None, ''):
            return integer(value)
    return 0

def title_of(row: Mapping[str, Any] | Any) -> str:
    return str(get_value(row, 'title', '') or '')

def query_rows(query: str) -> list[Any]:
    rows = list(search_runtime_knowledge(query, db_path=DB, limit=POOL_LIMIT))
    return rows

def build_features(query: str) -> list[ShadowCandidate]:
    rows = query_rows(query)
    if not rows:
        return []
    exact_rows = exact_feature_rows(query, rows)
    result: list[ShadowCandidate] = []
    for item in exact_rows:
        row = item['row']
        coverage = float(item['coverage'])
        rarity_coverage = float(item['rarity_coverage'])
        title_coverage = float(item['title_coverage'])
        numeric_identity = float(item['numeric_identity'])
        full_title_identity = float(item['full_title_identity'])
        bm25_position = float(item['bm25_position'])
        r7_score = float(item['r7_score'])
        r7_r4_score = WEIGHTS['coverage'] * coverage + WEIGHTS['rarity_coverage'] * rarity_coverage + WEIGHTS['title_coverage'] * title_coverage + WEIGHTS['numeric_identity'] * numeric_identity
        result.append(ShadowCandidate(document_id=document_id_of(row), chunk_id=chunk_id_of(row), title=title_of(row), production_rank=int(item['production_rank']), coverage=coverage, rarity_coverage=rarity_coverage, title_coverage=title_coverage, numeric_identity=numeric_identity, full_title_identity=full_title_identity, bm25_position=bm25_position, r7_score=r7_score, r7_r4_score=r7_r4_score))
    return result

def r7_r4_sort_key(item: ShadowCandidate) -> tuple[Any, ...]:
    return (-item.r7_r4_score, -item.coverage, -item.rarity_coverage, -item.title_coverage, -item.numeric_identity, -item.full_title_identity, item.production_rank, item.document_id, item.chunk_id)

def rank_query(query: str) -> list[ShadowCandidate]:
    return sorted(build_features(query), key=r7_r4_sort_key)

def target_rank(ranked: Iterable[ShadowCandidate], document_id: int) -> int | None:
    for rank, item in enumerate(ranked, start=1):
        if item.document_id == document_id:
            return rank
    return None

def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))
r3_rows = read_tsv(R3)
if len(r3_rows) != 250:
    raise RuntimeError(f'R3 population is {len(r3_rows)}, expected 250')

def first_present(row: Mapping[str, str], names: Iterable[str]) -> str:
    for name in names:
        value = row.get(name, '')
        if value not in (None, ''):
            return str(value)
    return ''
r3_detail: list[dict[str, Any]] = []
resolved = 0
top20 = 0
top100 = 0
regressions = 0
for index, source in enumerate(r3_rows, start=1):
    query = first_present(source, ('query', 'search_query', 'test_query'))
    expected_document = integer(first_present(source, ('document_id', 'target_document_id', 'expected_document_id')))
    if not query:
        raise RuntimeError(f'R3 row {index}: query unavailable')
    if expected_document <= 0:
        raise RuntimeError(f'R3 row {index}: document identity unavailable')
    ranked = rank_query(query)
    rank = target_rank(ranked, expected_document)
    old_rank = integer(first_present(source, ('shadow_rank', 'r7_rank', 'rank', 'qualified_rank', 'production_rank')), 0)
    if rank is not None:
        resolved += 1
        if rank <= 20:
            top20 += 1
        if rank <= 100:
            top100 += 1
        if old_rank > 0 and rank > old_rank:
            regressions += 1
    r3_detail.append({'sample_index': index, 'query': query, 'document_id': expected_document, 'previous_rank': old_rank or '', 'r7_r4_rank': rank or '', 'resolved': rank is not None, 'top20': rank is not None and rank <= 20, 'top100': rank is not None and rank <= 100, 'regressed': rank is not None and old_rank > 0 and (rank > old_rank)})
target_ranked = rank_query(TARGET_QUERY)
target_position = target_rank(target_ranked, TARGET_DOCUMENT)
target_item = next((item for item in target_ranked if item.document_id == TARGET_DOCUMENT), None)
if target_item is None:
    raise RuntimeError('79286 not generated')

def resolve_sequence(names: Iterable[str]) -> list[Any]:
    for name in names:
        value = getattr(r7, name, None)
        if isinstance(value, (list, tuple)):
            return list(value)
    return []
r6_cases = resolve_sequence(('R6_CANARIES', 'R6_CASES', 'HARD_CANARIES'))
identity_cases = resolve_sequence(('IDENTITY_CANARIES', 'IDENTITY_CASES'))
semantic_cases = resolve_sequence(('SEMANTIC_CONTROLS', 'SEMANTIC_CASES'))
adversarial_cases = resolve_sequence(('ADVERSARIAL_CONTROLS', 'ADVERSARIAL_CASES'))

def case_value(case: Any, names: Iterable[str], default: Any='') -> Any:
    if isinstance(case, Mapping):
        for name in names:
            if name in case:
                return case[name]
    for name in names:
        if hasattr(case, name):
            return getattr(case, name)
    return default

def run_rank_cases(cases: list[Any]) -> list[dict[str, Any]]:
    output = []
    for index, case in enumerate(cases, start=1):
        query = str(case_value(case, ('query', 'search_query'), ''))
        document_id = integer(case_value(case, ('document_id', 'target_document_id', 'expected_document_id'), 0))
        if not query or document_id <= 0:
            output.append({'index': index, 'query': query, 'document_id': document_id, 'rank': '', 'valid_contract': False})
            continue
        ranked = rank_query(query)
        rank = target_rank(ranked, document_id)
        output.append({'index': index, 'query': query, 'document_id': document_id, 'rank': rank or '', 'valid_contract': True, 'top20': rank is not None and rank <= 20})
    return output
r6_results = run_rank_cases(r6_cases)
identity_results = run_rank_cases(identity_cases)
semantic_results = run_rank_cases(semantic_cases)
adversarial_results = []
for index, case in enumerate(adversarial_cases, start=1):
    query = str(case_value(case, ('query', 'search_query'), ''))
    forbidden_document = integer(case_value(case, ('document_id', 'forbidden_document_id', 'target_document_id'), 0))
    if not query:
        adversarial_results.append({'index': index, 'query': '', 'forbidden_document_id': forbidden_document, 'accepted': False, 'valid_contract': False})
        continue
    ranked = rank_query(query)
    rank = target_rank(ranked, forbidden_document) if forbidden_document > 0 else None
    accepted = rank is not None and rank <= 20
    adversarial_results.append({'index': index, 'query': query, 'forbidden_document_id': forbidden_document, 'rank': rank or '', 'accepted': accepted, 'valid_contract': True})
r6_valid = [row for row in r6_results if row.get('valid_contract')]
identity_valid = [row for row in identity_results if row.get('valid_contract')]
semantic_valid = [row for row in semantic_results if row.get('valid_contract')]
adversarial_valid = [row for row in adversarial_results if row.get('valid_contract')]
r6_top20 = sum((1 for row in r6_valid if row.get('top20')))
identity_top20 = sum((1 for row in identity_valid if row.get('top20')))
semantic_top20 = sum((1 for row in semantic_valid if row.get('top20')))
adversarial_accepts = sum((1 for row in adversarial_valid if row.get('accepted')))
uri = 'file:' + str(DB) + '?mode=ro'
connection = sqlite3.connect(uri, uri=True)
connection.execute('PRAGMA query_only = ON')
integrity = connection.execute('PRAGMA integrity_check').fetchone()[0]
connection.close()
certification = {'root_cause_contract': True, 'primary_weight_sum_097': math.isclose(EXPECTED_PRIMARY_MAX, 0.97, rel_tol=0.0, abs_tol=1e-15), 'bm25_removed_from_primary_score': True, 'bm25_retained_only_as_late_tiebreak': True, 'target_79286_resolved': target_position is not None, 'target_79286_top20': target_position is not None and target_position <= 20, 'r3_exact_250': len(r3_rows) == 250, 'r3_resolved_250': resolved == 250, 'r3_top100_250': top100 == 250, 'r3_top20_at_least_245': top20 >= 245, 'r3_zero_regressions': regressions == 0, 'r6_contract_exact_9': len(r6_valid) == 9, 'r6_nine_top20': len(r6_valid) == 9 and r6_top20 == 9, 'identity_contract_exact_4': len(identity_valid) == 4, 'identity_four_top20': len(identity_valid) == 4 and identity_top20 == 4, 'semantic_contract_exact_4': len(semantic_valid) == 4, 'semantic_four_top20': len(semantic_valid) == 4 and semantic_top20 == 4, 'adversarial_zero_accepts': adversarial_accepts == 0, 'database_integrity': integrity == 'ok'}
shadow_certified = all(certification.values())

def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fieldnames = list(rows[0].keys())
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
write_tsv(R3_DETAIL, r3_detail)
write_tsv(R6_DETAIL, r6_results)
write_tsv(IDENTITY_DETAIL, identity_results)
write_tsv(SEMANTIC_DETAIL, semantic_results)
write_tsv(ADVERSARIAL_DETAIL, adversarial_results)
write_tsv(TARGET_DETAIL, [{**asdict(target_item), 'r7_r4_rank': target_position}])
source_contract = f'\nGENESIS RECALL R4-R10-R7-R4\nBM25 POSITION DEMOTION SHADOW CONTRACT\n\nCERTIFIED R7 ROOT CAUSE\n-----------------------\nBM25_POSITION_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER\n\nR7 PRIMARY SCORE\n----------------\n0.40 * coverage\n+ 0.27 * rarity_coverage\n+ 0.23 * title_coverage\n+ 0.07 * numeric_identity\n+ 0.03 * bm25_position\n\nR7-R4 PRIMARY SCORE\n-------------------\n0.40 * coverage\n+ 0.27 * rarity_coverage\n+ 0.23 * title_coverage\n+ 0.07 * numeric_identity\n\nPRIMARY MAX\n-----------\n{EXPECTED_PRIMARY_MAX}\n\nIMPORTANT\n---------\nThe remaining weights are NOT renormalized.\n\nbm25_position is not part of the R7-R4 primary score.\n\nProduction/BM25 position is retained only as a late\ndeterministic sort key after:\n  r7_r4_score\n  coverage\n  rarity_coverage\n  title_coverage\n  numeric_identity\n  full_title_identity\n\nNo production source is modified.\nNo qualification threshold is modified.\n'.strip()
SOURCE_CONTRACT.write_text(source_contract + '\n', encoding='utf-8')
trace_lines = ['GENESIS RECALL R4-R10-R7-R4 TRACE', '', f'target document: {TARGET_DOCUMENT}', f'target query: {TARGET_QUERY}', f'target rank: {target_position}', f'target R7 score: {target_item.r7_score}', f'target R7-R4 score: {target_item.r7_r4_score}', f'target production rank: {target_item.production_rank}', '', f'R3 population: {len(r3_rows)}', f'R3 resolved: {resolved}', f'R3 top20: {top20}', f'R3 top100: {top100}', f'R3 regressions: {regressions}', '', f'R6 contracts resolved: {len(r6_valid)}', f'R6 top20: {r6_top20}', '', f'identity contracts resolved: {len(identity_valid)}', f'identity top20: {identity_top20}', '', f'semantic contracts resolved: {len(semantic_valid)}', f'semantic top20: {semantic_top20}', '', f'adversarial accepts: {adversarial_accepts}', '', f'DB integrity: {integrity}', '', f'shadow certified: {shadow_certified}']
TRACE.write_text('\n'.join(trace_lines) + '\n', encoding='utf-8')
report = {'phase': 'R4-R10-R7-R4', 'name': 'BM25-Position Demotion Shadow Repair + Exact 250-Document Regression Certification', 'root_cause': 'BM25_POSITION_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER', 'repair': {'type': 'SHADOW_ONLY', 'primary_score': '0.40*coverage + 0.27*rarity_coverage + 0.23*title_coverage + 0.07*numeric_identity', 'primary_max': EXPECTED_PRIMARY_MAX, 'weights_renormalized': False, 'bm25_in_primary_score': False, 'bm25_role': 'LATE_DETERMINISTIC_TIEBREAK'}, 'target': {'document_id': TARGET_DOCUMENT, 'query': TARGET_QUERY, 'r7_r4_rank': target_position, 'production_rank': target_item.production_rank, 'r7_score': target_item.r7_score, 'r7_r4_score': target_item.r7_r4_score, 'coverage': target_item.coverage, 'rarity_coverage': target_item.rarity_coverage, 'title_coverage': target_item.title_coverage, 'numeric_identity': target_item.numeric_identity, 'full_title_identity': target_item.full_title_identity, 'bm25_position': target_item.bm25_position}, 'r3': {'population': len(r3_rows), 'resolved': resolved, 'top20': top20, 'top100': top100, 'regressions': regressions}, 'r6': {'expected': 9, 'resolved_contracts': len(r6_valid), 'top20': r6_top20}, 'identity': {'expected': 4, 'resolved_contracts': len(identity_valid), 'top20': identity_top20}, 'semantic': {'expected': 4, 'resolved_contracts': len(semantic_valid), 'top20': semantic_top20}, 'adversarial': {'cases': len(adversarial_valid), 'accepts': adversarial_accepts}, 'database_integrity': integrity, 'certification': certification, 'shadow_certified': shadow_certified}
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('=' * 78)
print(' GENESIS RECALL R4-R10-R7-R4 RESULT')
print('=' * 78)
print()
print('SHADOW REPAIR')
print('  bm25 in primary score       :', False)
print('  bm25 role                   :', 'LATE_DETERMINISTIC_TIEBREAK')
print('  remaining weights normalized:', False)
print('  primary max                 :', EXPECTED_PRIMARY_MAX)
print()
print('TARGET 79286')
print('  R7-R4 rank                  :', target_position)
print('  production rank             :', target_item.production_rank)
print('  R7 score                    :', target_item.r7_score)
print('  R7-R4 semantic score        :', target_item.r7_r4_score)
print()
print('R3 EXACT 250')
print('  resolved                    :', f'{resolved}/250')
print('  top20                       :', f'{top20}/250')
print('  top100                      :', f'{top100}/250')
print('  regressions                 :', regressions)
print()
print('R6 HARD CANARIES')
print('  contracts resolved          :', f'{len(r6_valid)}/9')
print('  top20                       :', f'{r6_top20}/9')
print()
print('IDENTITY CANARIES')
print('  contracts resolved          :', f'{len(identity_valid)}/4')
print('  top20                       :', f'{identity_top20}/4')
print()
print('SEMANTIC CONTROLS')
print('  contracts resolved          :', f'{len(semantic_valid)}/4')
print('  top20                       :', f'{semantic_top20}/4')
print()
print('ADVERSARIAL')
print('  accepts                     :', adversarial_accepts)
print()
print('CERTIFICATION')
for key, value in certification.items():
    print(f'  {key:<40}: {value}')
print()
print('R7-R4 SHADOW CERTIFIED       :', shadow_certified)
print()
print('DB integrity                 :', integrity)
print()
print('Artifacts:')
for path in (REPORT, R3_DETAIL, R6_DETAIL, IDENTITY_DETAIL, SEMANTIC_DETAIL, ADVERSARIAL_DETAIL, TARGET_DETAIL, TRACE, SOURCE_CONTRACT):
    print(' ', path)
print('=' * 78)
raise SystemExit(0 if shadow_certified else 1)

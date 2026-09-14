"""Evidence-based disk-space command advice. No disk scan is executed."""
from __future__ import annotations
import os
import re
import shutil
import subprocess


def supports_df(text):
    text = str(text or '').lower()
    # Require command semantics in a nearby passage, not a filename or topic tag.
    return bool(re.search(r'\bdf\b.{0,220}\b(?:file system|filesystem|disk)\b.{0,120}\b(?:space|usage)\b', text, re.S)
                or re.search(r'\b(?:disk|file system|filesystem)\s+(?:space|usage)\b.{0,220}\bdf\b', text, re.S))


def local_df_documentation(environment):
    if environment not in {'ubuntu','kali','linux'}:
        return {'status':'unavailable','reason':'No verified local command-help adapter for this platform.'}
    executable = shutil.which('df')
    if not executable:
        return {'status':'unavailable','reason':'df was not found on PATH.'}
    try:
        completed = subprocess.run(
            [executable, '--help'], shell=False, capture_output=True,
            text=True, errors='replace', timeout=5,
            env={**os.environ, 'LC_ALL':'C', 'LANG':'C'},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'status':'unavailable','reason':f'Local command help unavailable: {type(exc).__name__}'}
    text = completed.stdout[:32000]
    if completed.returncode or not (re.search(r'Usage:.*\bdf\b', text) and 'file system' in text.lower() and all(word in text.lower() for word in ('size', 'used', 'avail'))):
        return {'status':'unavailable','reason':'Installed df help did not establish command semantics.'}
    human = bool(re.search(r'-h,\s*--human-readable', text))
    return {'status':'available','source':executable+' --help','excerpt':text,'human_readable':human}


def disk_command_answer(grounding, snapshot, documentation_provider=local_df_documentation):
    environment = snapshot['environment']
    # Cross-platform command syntax is asserted only for the verified Linux adapter.
    if environment not in {'ubuntu','kali','linux'}:
        return {'answer':'I have not verified a disk-space command for this server platform yet.',
                'technical_details':{'route':'disk_command','status':'gap','environment':environment}}
    relevant = [item for item in (grounding.evidence if grounding else ())
                if supports_df(item.excerpt)]
    rejected = len(grounding.evidence) - len(relevant) if grounding else 0
    if relevant:
        evidence = relevant[0]
        return {'answer':f"Use `df` to show filesystem disk-space usage. [L1]\n\n[L1] Local catalog: {evidence.source_path}",
                'technical_details':{'route':'disk_command','source_kind':'catalog',
                  'evidence':evidence.to_dict(),'irrelevant_records_excluded':rejected}}
    local = documentation_provider(environment)
    if local['status'] == 'available':
        command = 'df -h' if local['human_readable'] else 'df'
        detail = ' in human-readable units' if local['human_readable'] else ''
        return {'answer':f"Use `{command}` to show filesystem disk-space usage{detail}. [L1]\n\n[L1] Installed command documentation: `{local['source']}`. Only help text was read; disk usage was not measured.",
                'technical_details':{'route':'disk_command','source_kind':'installed_command_help',
                  'documentation':local,'irrelevant_records_excluded':rejected,
                  'catalog_status':grounding.status if grounding else 'unavailable'}}
    return {'answer':'I could not verify a disk-space command from relevant catalog passages or installed command help. '+local['reason'],
            'technical_details':{'route':'disk_command','status':'gap','documentation':local,'irrelevant_records_excluded':rejected}}

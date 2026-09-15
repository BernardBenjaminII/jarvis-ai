"""Read-only binary inspection. Never launches discovered executables."""
import hashlib
import os
import shutil
from pathlib import Path

NAMES = ('nmap', 'amass', 'httpx', 'subfinder', 'katana', 'nuclei', 'docker', 'ollama')
MARKER = b'github.com/projectdiscovery/httpx'


def inspect_httpx(path):
    result = {'path': str(path), 'identity': 'unverified', 'recon_available': False,
              'executed': False, 'ready_for_live_testing': False}
    try:
        path = Path(path).resolve(strict=True)
        result['resolved_path'] = str(path)
        if not path.is_file() or not os.access(path, os.X_OK):
            result['reason'] = 'Not an executable regular file'
            return result
        # Bound disk reads; unrecognized/large files fail closed.
        if path.stat().st_size > 128 * 1024 * 1024:
            result['reason'] = 'Inspection size limit exceeded'
            return result
        digest = hashlib.sha256()
        marker = False
        prefix = b''
        tail = b''
        with path.open('rb') as stream:
            while chunk := stream.read(65536):
                if not prefix:
                    prefix = chunk
                digest.update(chunk)
                marker = marker or MARKER in tail + chunk
                tail = chunk[-len(MARKER):]
        result['sha256'] = digest.hexdigest()
        if prefix.startswith(b'#!') and (b'from httpx import' in prefix or b'import httpx' in prefix):
            result['identity'] = 'python-httpx-client'
            result['reason'] = 'Python client launcher; not the reconnaissance tool'
        elif prefix.startswith(b'\x7fELF') and marker:
            result['identity'] = 'projectdiscovery-httpx-binary-marker'
            result['recon_available'] = True
            result['reason'] = 'Static Go module marker; provenance and operational readiness not verified'
        else:
            result['reason'] = 'Unrecognized executable; wrapper scripts require explicit review'
    except OSError as error:
        result['reason'] = str(error)
    return result


def inventory():
    result = {}
    for name in NAMES:
        path = shutil.which(name)
        if name == 'httpx' and path:
            result[name] = inspect_httpx(path)
        else:
            result[name] = {'path': path, 'identity': 'unverified' if path else 'missing',
                            'executable_present': bool(path), 'executed': False,
                            'ready_for_live_testing': False}
    return result

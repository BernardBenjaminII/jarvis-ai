"""Local Linux credentials, outside Git. Permission-protected, not encrypted."""
import getpass
import json
import os
from pathlib import Path
import stat
import tempfile
from .hackerone import DiscoveryError


def location():
    return Path.home()/'.config/jarvis/bounty_credentials/hackerone.json'


def validate(username, token):
    if (not isinstance(username, str) or not isinstance(token, str)
            or not username or not token or ':' in username
            or len(username) > 512 or len(token) > 4096
            or any(ord(c) < 33 or ord(c) == 127 for c in username + token)):
        raise DiscoveryError('Invalid API identifier or token; credentials were not saved')
    return username, token


def check_directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise DiscoveryError('Credential directory must be owned by you with mode 700')


def save(username, token, path=None):
    username, token = validate(username, token)
    path = path or location()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    check_directory(path.parent)
    if path.is_symlink():
        raise DiscoveryError('Refusing a credential-file symlink')
    fd, temporary = tempfile.mkstemp(prefix='.credentials-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump({'username': username, 'token': token}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load(path=None):
    path = path or location()
    if not path.parent.exists():
        return None
    check_directory(path.parent)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError:
        raise DiscoveryError('Cannot safely open saved credentials') from None
    with os.fdopen(fd, 'r') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise DiscoveryError('Credential file must be owned by you, unlinked elsewhere, and mode 600')
        raw = stream.read(8193)
    try:
        if len(raw) > 8192:
            raise ValueError()
        data = json.loads(raw)
        return validate(data['username'], data['token'])
    except (ValueError, KeyError, TypeError):
        raise DiscoveryError('Saved credentials are invalid; run auth configure again') from None


def forget(path=None):
    path = path or location()
    if not path.parent.exists():
        return
    check_directory(path.parent)
    path.unlink(missing_ok=True)


def prompt():
    import sys
    if not sys.stdin.isatty():
        raise DiscoveryError('Run auth configure in an interactive terminal first')
    return validate(input('HackerOne API identifier: ').strip(),
                    getpass.getpass('HackerOne API token (hidden): '))


def resolve():
    saved = load()
    return saved if saved is not None else prompt()

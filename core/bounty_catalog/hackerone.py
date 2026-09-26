"""HackerOne researcher API, fixed host and GET-only listing endpoint."""
import base64
import http.client
import json
import re
import ssl
import time
from urllib.parse import urlencode, urlsplit, parse_qs

HOST = 'api.hackerone.com'
PATH = '/v1/hackers/programs'
MAX_BYTES = 2 * 1024 * 1024

class DiscoveryError(ValueError):
    pass


def page_url(page):
    return 'https://' + HOST + PATH + '?' + urlencode({'page[number]': page, 'page[size]': 100})


def decode(raw):
    if len(raw) > MAX_BYTES:
        raise DiscoveryError('Response exceeds 2 MiB')
    try:
        document = json.loads(raw)
    except (ValueError, UnicodeError):
        raise DiscoveryError('Invalid JSON response') from None
    if not isinstance(document, dict) or not isinstance(document.get('data'), list):
        raise DiscoveryError('Expected a program list')
    if len(document['data']) > 100:
        raise DiscoveryError('Unexpected page size')
    rows = []
    for item in document['data']:
        if not isinstance(item, dict) or item.get('type') != 'program':
            raise DiscoveryError('Expected program objects')
        a = item.get('attributes')
        if not isinstance(a, dict):
            raise DiscoveryError('Missing program attributes')
        handle = a.get('handle')
        if not isinstance(handle, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', handle):
            raise DiscoveryError('Invalid program handle')
        name = a.get('name')
        if not isinstance(name, str) or not name or len(name) > 500:
            raise DiscoveryError('Invalid program name')
        bounty = a.get('offers_bounties')
        if bounty is not None and type(bounty) is not bool:
            raise DiscoveryError('Invalid offers_bounties value')
        def field(key, limit=100):
            value = a.get(key)
            if value is not None and (not isinstance(value, str) or len(value) > limit):
                raise DiscoveryError('Invalid ' + key)
            return value
        rows.append({'handle': handle, 'name': name,
                     'program_url': 'https://hackerone.com/' + handle,
                     'reward_status': 'paid' if bounty is True else ('no_bounty' if bounty is False else 'unknown'),
                     'currency': field('currency'), 'submission_state': field('submission_state'),
                     'visibility': field('state'), 'source_updated_at': field('updated_at'),
                     'policy_text': field('policy', MAX_BYTES),
                     'reward_amount': None, 'testing_authorized': False})
    links = document.get('links', {})
    if not isinstance(links, dict):
        raise DiscoveryError('Invalid pagination links')
    return rows, links.get('next')


def next_page(link, current):
    if link is None:
        return None
    if not isinstance(link, str):
        raise DiscoveryError('Invalid next-page link')
    # Never follow server-supplied URLs. Validate, then generate our own request.
    parsed = urlsplit(link)
    if parsed.scheme != 'https' or parsed.netloc != HOST or parsed.path != PATH or parsed.fragment:
        raise DiscoveryError('Unexpected pagination destination')
    query = parse_qs(parsed.query)
    if set(query) - {'page[number]', 'page[size]'}:
        raise DiscoveryError('Unexpected pagination parameters')
    if query.get('page[number]') != [str(current + 1)]:
        raise DiscoveryError('Pagination is not sequential')
    if 'page[size]' in query and query['page[size]'] != ['100']:
        raise DiscoveryError('Unexpected pagination size')
    return current + 1


class Client:
    def __init__(self, username, token):
        if not username or not token or ':' in username:
            raise DiscoveryError('API username and token are required')
        self._auth = 'Basic ' + base64.b64encode((username + ':' + token).encode()).decode()

    def fetch(self, page):
        connection = http.client.HTTPSConnection(HOST, timeout=15, context=ssl.create_default_context())
        try:
            path = PATH + '?' + urlencode({'page[number]': page, 'page[size]': 100})
            connection.request('GET', path, headers={'Authorization': self._auth,
                'Accept': 'application/json', 'Accept-Encoding': 'identity',
                'User-Agent': 'Jarvis-Opportunity-Catalog/4'})
            response = connection.getresponse()
            if response.status != 200:
                # Do not expose credential-bearing request headers or response body.
                if response.status in (401, 403):
                    raise DiscoveryError('Authentication or API access rejected')
                if response.status == 429:
                    raise DiscoveryError('Rate limited; stopped without retry')
                raise DiscoveryError('API HTTP status ' + str(response.status))
            if response.getheader('Content-Encoding', 'identity') != 'identity':
                raise DiscoveryError('Unexpected response encoding')
            body = bytearray()
            deadline = time.monotonic() + 30
            while True:
                chunk = response.read1(min(65536, MAX_BYTES + 1 - len(body)))
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise DiscoveryError('Response exceeds 2 MiB')
                if time.monotonic() > deadline:
                    raise DiscoveryError('Response body deadline exceeded')
                if not chunk:
                    break
            return bytes(body)
        except (OSError, http.client.HTTPException):
            raise DiscoveryError('API connection failed; no automatic retry') from None
        finally:
            connection.close()

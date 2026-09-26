"""Own loopback HTTP fixture; no user-supplied destination or tool arguments."""
import http.server
import json
import secrets
import sys
import threading
from .runner import run_bounded

# Fixed client, explicit numeric loopback address, no redirects/proxies/DNS.
CLIENT = '''import http.client,sys
c=http.client.HTTPConnection("127.0.0.1",int(sys.argv[1]),timeout=2)
c.request("GET","/fixture/"+sys.argv[2])
r=c.getresponse()
body=r.read(4096)
c.close()
if r.status != 200 or body != b"JARVIS_R2_FIXTURE_OK":
    raise SystemExit("Fixture validation failed")
print(body.decode())
'''


def demo():
    token = secrets.token_hex(16)
    hits = []
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/fixture/' + token:
                self.send_error(404); return
            hits.append(self.path)
            body = b'JARVIS_R2_FIXTURE_OK'
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = run_bounded([sys.executable, '-I', '-c', CLIENT,
                              str(server.server_port), token])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    passed = result['state'] == 'completed' and result['output'].strip() == 'JARVIS_R2_FIXTURE_OK' and len(hits) == 1
    return {'mode': 'local_fixture_only', 'passed': passed,
            'network_activity': 'one HTTP request to an owned loopback fixture',
            'external_targets_tested': 0, 'fixture_requests': len(hits),
            'finding_status': 'not_a_vulnerability', 'execution': result}

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18991)
    args = parser.parse_args()
    expected = os.environ.get('RESEARCH_OS_MOCK_PROVIDER_KEY', 'ci-owner-provider-key')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def _authorized(self) -> bool:
            return self.headers.get('Authorization', '') == f'Bearer {expected}'

        def _json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self._authorized():
                self._json(401, {'error': 'unauthorized'}); return
            if self.path == '/v1/models':
                self._json(200, {'data': [{'id': 'mock-model'}]}); return
            self._json(404, {'error': 'not_found'})

        def do_POST(self):
            if not self._authorized():
                self._json(401, {'error': 'unauthorized'}); return
            if self.path != '/v1/chat/completions':
                self._json(404, {'error': 'not_found'}); return
            length = int(self.headers.get('Content-Length', '0') or '0')
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            messages = payload.get('messages', [])
            user_text = next((item.get('content', '') for item in reversed(messages) if item.get('role') == 'user'), '')
            self._json(200, {'choices': [{'message': {'content': f'mock-provider:{user_text}'}}]})

    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'mock provider ready on 127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()


if __name__ == '__main__':
    main()

"""Serve the public website and its local content editor."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import editor

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith('/api/'):
            if self.headers.get('Host', '').split(':')[0] not in ('localhost', '127.0.0.1'):
                self.send_json(403, {'error': 'Uporabite lokalni naslov.'})
            elif not editor.handle_get(self):
                self.send_json(404, {'error': 'Neznana povezava.'})
        else:
            super().do_GET()

    def do_POST(self):
        editor.handle_post(self)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT / 'public')))
    except OSError as error:
        parser.exit(1, f'Cannot start local server on port {args.port}: {error}\n')
    print(f'Local: http://127.0.0.1:{server.server_port}\nEditor: http://127.0.0.1:{server.server_port}/urejevalnik/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()

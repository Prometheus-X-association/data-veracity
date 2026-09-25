#!/usr/bin/env python3
"""
Serve the attestation demo page and proxy its API calls to the test network.

The DVA API sends no CORS headers, so a page opened straight from disk cannot
read its responses. This server puts the page and the APIs on one origin:

    /                 -> index.html next to this script
    /provider/...     -> provider DVA API   (default http://localhost:9091)
    /vla-manager/...  -> VLA Manager API    (default http://localhost:8000)

Usage: python3 serve.py [--port 8765] [--provider URL] [--vla-manager URL]

_Authored by Claude Code_ – 2026-09-25, for a one-off demo of POST /attestation
(branch yassine-refactor). Standard library only.
"""

import argparse
import http.server
import pathlib
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
UPSTREAMS: dict[str, str] = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            body = (HERE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def _proxy(self) -> None:
        prefix, _, rest = self.path.lstrip("/").partition("/")
        base = UPSTREAMS.get(prefix)
        if base is None:
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(base.rstrip("/") + "/" + rest, data=body, method=self.command)
        if ctype := self.headers.get("Content-Type"):
            req.add_header("Content-Type", ctype)
        req.add_header("Accept", self.headers.get("Accept", "*/*"))
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self._relay(resp.status, resp.headers.get("Content-Type"), resp.read())
        except urllib.error.HTTPError as e:
            self._relay(e.code, e.headers.get("Content-Type"), e.read())
        except (urllib.error.URLError, OSError) as e:
            msg = f'{{"title":"Upstream unreachable","detail":"{base}: {e}"}}'.encode()
            self._relay(502, "application/problem+json", msg)

    def _relay(self, status: int, ctype: str | None, body: bytes) -> None:
        self.send_response(status)
        if ctype:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--provider", default="http://localhost:9091")
    ap.add_argument("--vla-manager", default="http://localhost:8000")
    args = ap.parse_args()
    UPSTREAMS.update({"provider": args.provider, "vla-manager": args.vla_manager})
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Attestation demo on http://localhost:{args.port}/  (provider API: {args.provider})")
    server.serve_forever()


if __name__ == "__main__":
    main()

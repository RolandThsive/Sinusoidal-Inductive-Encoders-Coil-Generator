"""Test server for the Web GUI: makes the site the way GitHub Pages gets it (WebGUI/tools/build_site.py, into
LocalTesting/_site) and serves it with caching turned off, on the first free port from 8000."""
import functools
import http.server
import os
import socket
import subprocess
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                                  # the repository root: Generators/ and WebGUI/ sit here
SITE = os.path.join(HERE, "_site")                            # made new at every start; never committed


class NoCache(http.server.SimpleHTTPRequestHandler):
    # the types are named here: on some Windows computers .js is registered as plain text, which a browser refuses
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".json": "application/json",
                      ".wasm": "application/wasm", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".zip": "application/zip"}

    def end_headers(self):
        # the browser must always load the files of this folder, never an older copy it kept
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, *args):
        pass


def free_port(start=8000):
    for port in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    sys.exit("No free port between 8000 and 8049")


built = subprocess.run([sys.executable, os.path.join(REPO, "WebGUI", "tools", "build_site.py"), "--out", SITE])
if built.returncode != 0:
    sys.exit("The site could not be made (see the message above).")
port = free_port()
url = f"http://localhost:{port}/WebGUI/"
server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(NoCache, directory=SITE))
print(f"Serving {SITE}")
print(f"Open {url}   (close this window or press Ctrl+C to stop)")
webbrowser.open(url)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass

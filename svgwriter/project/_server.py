"""
``svgwriter preview``: a local page that rebuilds the project when a file changes and reloads itself.
"""

from __future__ import annotations

import html
import threading
import traceback
import webbrowser
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ._constants import POLL_SECONDS, RELOAD_MILLISECONDS, RELOAD_SCRIPT, WATCH_IGNORED
from ._gallery import gallery

__all__ = ["LiveServer", "snapshot"]


def snapshot(root: Path) -> dict[Path, float]:
    """Modification times of the project's files, outputs and caches left out."""
    times = {}
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if path.is_file() and not WATCH_IGNORED.intersection(parts):
            times[path] = path.stat().st_mtime
    return times


class LiveServer:
    """Serve the outputs of *build* at ``http://127.0.0.1:<port>``, rebuilding whenever a file under *root* changes."""

    def __init__(self, root: Path, build: Callable[[], list[Path]], title: str, port: int) -> None:
        self.root, self.build, self.title = root, build, title
        self.version, self.page = 0, ""
        self.stopped = threading.Event()
        self.server = ThreadingHTTPServer(("127.0.0.1", port), self._handler())

    @property
    def url(self) -> str:
        """Where the page is served."""
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}/"

    def rebuild(self) -> None:
        """Build again and publish the new page (or the error) under a new version."""
        try:
            body = gallery(self.build(), self.title)
        except Exception:
            body = f"<h3>{html.escape(self.title)}: build failed</h3><pre>{html.escape(traceback.format_exc())}</pre>"
        self.version += 1
        script = RELOAD_SCRIPT.format(version=self.version, interval=RELOAD_MILLISECONDS)
        self.page = f"<!doctype html><meta charset='utf-8'><title>{html.escape(self.title)}</title>{body}{script}"

    def _watch(self) -> None:
        seen = snapshot(self.root)
        while not self.stopped.wait(POLL_SECONDS):
            current = snapshot(self.root)
            if current != seen:
                seen = current
                self.rebuild()

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        live = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                text = str(live.version) if self.path == "/version" else live.page
                data = text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain" if self.path == "/version" else "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format: str, *args: object) -> None:
                pass

        return Handler

    def serve(self, open_browser: bool = True) -> None:
        """Build, open the page and serve until interrupted (Ctrl+C)."""
        self.rebuild()
        watcher = threading.Thread(target=self._watch, daemon=True)
        watcher.start()
        if open_browser:
            webbrowser.open(self.url)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stopped.set()
            self.server.server_close()

    def close(self) -> None:
        """Stop serving; call it from another thread than :meth:`serve`."""
        self.stopped.set()
        self.server.shutdown()

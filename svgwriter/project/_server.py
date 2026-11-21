"""
``svgwriter preview``: a local page that rebuilds the project when a file changes or a control moves.
"""

from __future__ import annotations

import html
import json
import threading
import traceback
import webbrowser
from collections.abc import Callable, Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from ..widgets import Control
from ._constants import POLL_SECONDS, RELOAD_MILLISECONDS, RELOAD_SCRIPT, WATCH_IGNORED
from ._form import controls_form, readouts
from ._gallery import gallery

__all__ = ["LiveServer", "snapshot"]

Build = Callable[[Mapping[str, Any]], list[Path]]
Controls = Callable[[], Mapping[str, Control]]


def snapshot(root: Path) -> dict[Path, float]:
    """Modification times of the project's files, outputs and caches left out."""
    times = {}
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if path.is_file() and not WATCH_IGNORED.intersection(parts):
            times[path] = path.stat().st_mtime
    return times


def _kept(controls: Mapping[str, Control], values: Mapping[str, Any]) -> dict[str, Any]:
    """The *values* that still name a control and pass its check."""
    kept = {}
    for name, value in values.items():
        if name in controls:
            try:
                kept[name] = controls[name].check(value)
            except (TypeError, ValueError):
                continue
    return kept


class LiveServer:
    """Serve the outputs of *build* at ``http://127.0.0.1:<port>``, rebuilding when a file under *root* changes.

    *build* takes the control values; *controls* lists the controls to show as a form, read again on
    every rebuild so edits to their declaration appear. Posting JSON values to ``/values`` rebuilds with
    them and answers with the new outputs. A failed build keeps the last outputs that worked, with the
    traceback under them.
    """

    def __init__(self, root: Path, build: Build, title: str, port: int, *, controls: Controls | None = None) -> None:
        self.root, self.build, self.title, self.controls = root, build, title, controls
        self.version, self.page = 0, ""
        self.values: dict[str, Any] = {}
        self.fields: Mapping[str, Control] = {}
        self.outputs, self.error = "", ""
        self._built: tuple[int, str] | None = None
        self._files = 0
        self._lock = threading.Lock()
        self.stopped = threading.Event()
        self.server = ThreadingHTTPServer(("127.0.0.1", port), self._handler())

    @property
    def url(self) -> str:
        """Where the page is served."""
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}/"

    def rebuild(self, *, files_changed: bool = True) -> None:
        """Build again with the current values and publish the new page (or the error) under a new version.

        The controls are read again only when files changed; the same files and values are not built twice.
        """
        with self._lock:
            try:
                if files_changed:
                    self._files += 1
                    self.fields = dict(self.controls()) if self.controls is not None else {}
                    self.values = _kept(self.fields, self.values)
                key = (self._files, json.dumps(self.values, sort_keys=True, default=repr))
                if key != self._built:
                    self.outputs = gallery(self.build(dict(self.values)), self.title)
                    self._built = key
                self.error = ""
            except Exception:
                self.error = (f"<h3>{html.escape(self.title)}: build failed</h3>"
                              f"<pre class='svgwriter-error'>{html.escape(traceback.format_exc())}</pre>")
            self.version += 1
            script = RELOAD_SCRIPT.format(version=self.version, interval=RELOAD_MILLISECONDS)
            form = controls_form(self.fields, self.values)
            self.page = (f"<!doctype html><meta charset='utf-8'><title>{html.escape(self.title)}</title>{form}"
                         f"<div id='svgwriter-outputs'>{self.shown}</div>{script}")

    @property
    def shown(self) -> str:
        """The outputs and, after a failed build, the error under them."""
        return self.outputs + self.error

    def submit(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Take values posted by the form (as :meth:`Control.from_form` reads them) and rebuild.

        Returns the JSON answer: the new version, outputs and readouts, or ``{"error": ...}`` for a bad value.
        """
        values = dict(self.values)
        for name, sent in raw.items():
            control = self.fields.get(name)
            if control is None:
                return {"error": f"no control {name!r}"}
            try:
                values[name] = control.from_form(sent)
            except (TypeError, ValueError) as error:
                return {"error": f"{control.label or name}: {error}"}
        self.values = values
        self.rebuild(files_changed=False)
        return {"version": self.version, "outputs": self.shown, "readouts": readouts(self.fields, self.values)}

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
            def _send(self, status: int, kind: str, text: str) -> None:
                data = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", kind)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                if self.path == "/version":
                    self._send(200, "text/plain", str(live.version))
                else:
                    self._send(200, "text/html; charset=utf-8", live.page)

            def do_POST(self) -> None:
                if self.path != "/values":
                    self._send(404, "text/plain", "not found")
                    return
                try:
                    raw = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                except ValueError as error:
                    self._send(400, "application/json", json.dumps({"error": f"not JSON: {error}"}))
                    return
                if not isinstance(raw, dict):
                    self._send(400, "application/json", json.dumps({"error": "expected a JSON object"}))
                    return
                answer = live.submit(raw)
                self._send(400 if "error" in answer else 200, "application/json", json.dumps(answer))

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

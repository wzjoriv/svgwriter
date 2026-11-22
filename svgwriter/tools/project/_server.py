"""
``svgwriter preview``: a local page that redraws the project as its controls move and its files change.

Control changes draw only what the page shows, in memory; the output files are written by the page's
Build outputs button and after a file is saved.
"""

from __future__ import annotations

import html
import json
import threading
import time
import traceback
from collections.abc import Mapping, Sequence
from contextlib import ExitStack, nullcontext
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from ..._internal import _platform
from ...model.theme import Theme
from ...motion.video import Scene
from ..widgets import Control, controls_of
from ._build import View, page_views, scene_views, write_outputs
from ._config import ProjectConfig, read_config
from ._constants import (
    BACKGROUNDS,
    BUILD_IDLE_SECONDS,
    DISCONNECTS,
    MILLISECONDS,
    NOTEBOOK_SUFFIX,
    PAGE_SCRIPT,
    PAGE_STYLE,
    PAGE_TEMPLATE,
    POLL_SECONDS,
    VERSION_POLL_MS,
    WATCH_IGNORED,
)
from ._entry import (
    Item,
    entry_parts,
    items_of,
    load_object,
    load_theme,
    project_scope,
    register_fonts,
    working_directory,
)
from ._form import controls_form, readouts

__all__ = ["LiveProject", "LiveServer", "snapshot"]


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


class LiveProject:
    """A project's code imported once and drawn in memory as often as asked, until :meth:`load` imports it again.

    While loaded, the project's modules stay imported and its folder is the current folder; :meth:`close`
    forgets both.

    Parameters
    ----------
    root : pathlib.Path
        The project folder.

    Examples
    --------
    >>> import svgwriter as svg, tempfile
    >>> from svgwriter.tools.project._server import LiveProject
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     live = LiveProject(svg.Project.new(f"{folder}/card").root)
    ...     _ = live.load()
    ...     print([view.name for view in live.render({})])
    ...     live.close()
    ['card']
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.config: ProjectConfig = read_config(root)
        self._items: list[Item] = []
        self._theme: Theme | None = None
        self._scenes: list[View] = []
        self._scope = ExitStack()

    @property
    def notebook(self) -> bool:
        """Whether the entry lives in a notebook, which runs in its own kernel on every build."""
        return entry_parts(self.config)[0].endswith(NOTEBOOK_SUFFIX)

    def load(self) -> dict[str, Control]:
        """Import the project's current files and return the controls its page functions declare."""
        self.close()
        self.config = read_config(self.root)
        register_fonts(self.config)
        self._theme = load_theme(self.config)
        if self.notebook:
            return {}
        self._scope.enter_context(working_directory(self.root))
        self._scope.enter_context(project_scope(self.root))
        with self._theme if self._theme is not None else nullcontext():
            self._items = items_of(self.config, load_object(self.config))
        self._scenes = scene_views(self.config, self._items, self._theme)
        found: dict[str, Control] = {}
        for item in self._items:
            if not isinstance(item, (Scene, type)):
                found.update(controls_of(item, infer=False))
        return found

    def render(self, values: Mapping[str, Any]) -> list[View]:
        """The SVG of every page drawn with *values*, then every scene; no file is written.

        A notebook entry has no importable code, so it is built in its kernel and its SVG outputs are read back.
        """
        if self.notebook:
            from .project import Project

            return [View(path.stem, path.read_text(encoding="utf-8"))
                    for path in Project(self.config).build(["svg"]) if path.suffix == ".svg"]
        return page_views(self.config, self._items, self._theme, values) + self._scenes

    def build(self, values: Mapping[str, Any], formats: Sequence[str] | None = None) -> list[Path]:
        """Write the output files with *values*: *formats*, or those of ``[outputs]``."""
        chosen = formats if formats is not None else self.config.formats
        if self.notebook:
            from .project import Project

            return Project(self.config).build(chosen, values=values)
        return write_outputs(self.config, self._items, self._theme, chosen, values)

    def close(self) -> None:
        """Forget the imported modules and go back to the folder that was current before :meth:`load`."""
        self._scope.close()
        self._items, self._scenes = [], []


class LiveServer:
    """Serve a page showing *live*'s drawings at ``http://127.0.0.1:<port>``, redrawn as controls move and files change.

    Posting JSON values to ``/values`` draws the shown pages again in memory and answers with them. Requests
    arriving during a drawing are coalesced: the latest values win and one drawing answers them all.
    ``/build`` writes the output files, as does a file save once the project has been quiet for a moment
    (``[preview] build_on_save``). A failed drawing keeps the last drawings that worked, with the traceback.

    Parameters
    ----------
    live : LiveProject
        The project, not yet loaded.
    port : int
        The local port; 0 picks a free one.
    """

    def __init__(self, live: LiveProject, port: int) -> None:
        self.live = live
        self.title = live.config.name
        self.version = 0
        self.fields: dict[str, Control] = {}
        self.values: dict[str, Any] = {}
        self.views: list[View] = []
        self.error = ""
        self.milliseconds = 0
        self._wanted: dict[str, Any] = {}
        self._asked = self._drawn = 0
        self._unloaded = False
        self._lock = threading.Lock()
        self._pending = threading.Lock()
        self.stopped = threading.Event()
        self.server = ThreadingHTTPServer(("127.0.0.1", port), self._handler())

    @property
    def url(self) -> str:
        """Where the page is served."""
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}/"

    def _shown(self, views: list[View]) -> list[View]:
        chosen = self.live.config.preview.pages
        if chosen is None:
            return views
        named = {view.name: view for view in views}
        missing = [name for name in chosen if name not in named]
        if missing:
            raise ValueError(f"{self.live.config.source}: preview.pages names {', '.join(map(repr, missing))}; "
                             f"the project draws {', '.join(map(repr, named))}")
        return [named[name] for name in chosen]

    def _draw(self, values: dict[str, Any]) -> None:
        """Draw with *values* (holding the lock); a failure keeps the last drawings and records the traceback."""
        start = time.perf_counter()
        self.values = values
        if self._unloaded:
            return
        try:
            self.views = self._shown(self.live.render(values))
            self.error = ""
        except Exception:
            self.error = traceback.format_exc()
        self.milliseconds = round((time.perf_counter() - start) * MILLISECONDS)

    def reload(self) -> None:
        """Import the project's files again, read its controls and draw; the page picks it up as a new version."""
        with self._lock:
            try:
                self.fields = self.live.load()
            except Exception:
                self.error = traceback.format_exc()
                self._unloaded = True
            else:
                self._unloaded = False
                with self._pending:
                    self._wanted = _kept(self.fields, self._wanted)
                    values = dict(self._wanted)
                self._draw(values)
            self.version += 1

    def submit(self, raw: Mapping[str, Any]) -> tuple[int, dict[str, Any]]:
        """Take values posted by the form (as :meth:`Control.from_form` reads them) and draw with the latest values.

        Returns the HTTP status and the JSON answer: :meth:`state`, or ``{"error": ...}`` for a bad value.
        """
        with self._pending:
            values = dict(self._wanted)
            for name, sent in raw.items():
                control = self.fields.get(name)
                if control is None:
                    return 400, {"error": f"no control {name!r}"}
                try:
                    values[name] = control.from_form(sent)
                except (TypeError, ValueError) as error:
                    return 400, {"error": f"{control.label or name}: {error}"}
            self._wanted = values
            self._asked += 1
            ticket = self._asked
        with self._lock:
            if self._drawn < ticket:
                with self._pending:
                    latest, newest = dict(self._wanted), self._asked
                self._draw(latest)
                self._drawn = newest
            return 200, self.state()

    def build(self) -> dict[str, Any]:
        """Write the output files with the current values; the JSON answer names them, or the error."""
        start = time.perf_counter()
        with self._lock:
            try:
                written = self.live.build(self.values, self.live.config.preview.formats_on_build)
            except Exception:
                return {"error": traceback.format_exc()}
        return {"files": [path.name for path in written],
                "ms": round((time.perf_counter() - start) * MILLISECONDS)}

    def state(self, *, form: bool = False) -> dict[str, Any]:
        """What the page shows, as JSON: the drawings, the error, the readouts, and with *form* the controls."""
        answer: dict[str, Any] = {"version": self.version, "views": [view._asdict() for view in self.views],
                                  "error": self.error, "ms": self.milliseconds,
                                  "readouts": readouts(self.fields, self.values)}
        if form:
            answer["form"] = controls_form(self.fields, self.values)
        return answer

    def page(self) -> str:
        """The whole page, with the current state inside it."""
        preview = self.live.config.preview
        state = {**self.state(form=True), "debounce": preview.debounce_ms, "poll": VERSION_POLL_MS}
        custom = preview.background not in BACKGROUNDS
        backdrop = "custom" if custom else preview.background
        style = f" style='background:{html.escape(preview.background)}'" if custom else ""
        return PAGE_TEMPLATE.format(
            title=html.escape(self.title), style=PAGE_STYLE, layout=preview.layout, fit=preview.fit,
            backdrop=backdrop, backdrop_style=style, panel_hidden="" if self.fields else " hidden",
            form=state["form"], state=json.dumps(state).replace("</", "<\\/"), script=PAGE_SCRIPT)

    def _watch(self) -> None:
        seen = snapshot(self.live.root)
        due: float | None = None
        while not self.stopped.wait(POLL_SECONDS):
            current = snapshot(self.live.root)
            if current != seen:
                seen = current
                self.reload()
                due = time.monotonic() + BUILD_IDLE_SECONDS if self.live.config.preview.build_on_save else None
            elif due is not None and time.monotonic() >= due:
                due = None
                self.build()

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        live = self

        class Handler(BaseHTTPRequestHandler):
            def handle(self) -> None:
                try:
                    super().handle()
                except DISCONNECTS:
                    self.close_connection = True

            def finish(self) -> None:
                try:
                    super().finish()
                except DISCONNECTS:
                    pass

            def _send(self, status: int, kind: str, text: str) -> None:
                data = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", kind)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _json(self, status: int, answer: Mapping[str, Any]) -> None:
                self._send(status, "application/json", json.dumps(answer))

            def do_GET(self) -> None:
                if self.path == "/version":
                    self._send(200, "text/plain", str(live.version))
                elif self.path == "/state":
                    self._json(200, live.state(form=True))
                else:
                    self._send(200, "text/html; charset=utf-8", live.page())

            def do_POST(self) -> None:
                if self.path == "/build":
                    answer = live.build()
                    self._json(500 if "error" in answer else 200, answer)
                    return
                if self.path != "/values":
                    self._send(404, "text/plain", "not found")
                    return
                try:
                    raw = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                except ValueError as error:
                    self._json(400, {"error": f"not JSON: {error}"})
                    return
                if not isinstance(raw, dict):
                    self._json(400, {"error": "expected a JSON object"})
                    return
                self._json(*live.submit(raw))

            def log_message(self, format: str, *args: object) -> None:
                pass

        return Handler

    def serve(self, open_browser: bool = True) -> None:
        """Load and draw the project, open the page and serve until interrupted (Ctrl+C)."""
        self.reload()
        watcher = threading.Thread(target=self._watch, daemon=True)
        watcher.start()
        if open_browser:
            _platform.open_browser(self.url)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stopped.set()
            self.server.server_close()
            with self._lock:
                self.live.close()

    def close(self) -> None:
        """Stop serving; call it from another thread than :meth:`serve`."""
        self.stopped.set()
        self.server.shutdown()

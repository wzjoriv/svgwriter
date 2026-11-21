from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.tools.project import PreviewConfig, ProjectError
from svgwriter.tools.project._server import LiveProject, LiveServer

MAIN = '''import svgwriter as svg


@svg.widgets.controls(size=(10, 80), shape=["box", "dot"])
def build(doc, size=20, shape="box"):
    if size > 70:
        raise RuntimeError("too big on purpose")
    if shape == "box":
        doc.rect(0, 0, size, size, fill="#0ea5e9")
    else:
        doc.circle(size, size, size, fill="#0ea5e9")


class Spin(svg.Scene):
    duration = 1.0

    def build(self, doc):
        self.box = doc.rect(0, 0, 10, 10)

    def update(self, seconds):
        self.box.x = 10 * seconds


outputs = [build, Spin]
'''
PREVIEW = '''
[preview]
build_on_save = {build_on_save}
'''
WAIT = 20


@pytest.fixture
def root(tmp_path: Path) -> Path:
    made = svg.Project.new(tmp_path / "knobs")
    (made.root / "main.py").write_text(MAIN, encoding="utf-8")
    manifest = made.root / "svgwriter.toml"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace('"main:build"', '"main:outputs"')
                        + PREVIEW.format(build_on_save="false"), encoding="utf-8")
    return made.root


@pytest.fixture
def server(root: Path) -> Iterator[LiveServer]:
    live = LiveServer(LiveProject(root), 0)
    thread = threading.Thread(target=live.serve, kwargs={"open_browser": False}, daemon=True)
    thread.start()
    deadline = time.monotonic() + WAIT
    while live.version == 0:
        assert time.monotonic() < deadline
        time.sleep(0.05)
    yield live
    live.close()
    thread.join(5)


def _post(url: str, body: bytes, timeout: float = WAIT) -> tuple[int, dict]:
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return answer.status, json.loads(answer.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def _values(server: LiveServer, values: dict, timeout: float = WAIT) -> tuple[int, dict]:
    return _post(server.url + "values", json.dumps(values).encode(), timeout)


def _outputs(root: Path) -> list[str]:
    return sorted(path.name for path in (root / "output").glob("*")) if (root / "output").is_dir() else []


def test_page_and_values(server: LiveServer, root: Path) -> None:
    page = urllib.request.urlopen(server.url).read().decode("utf-8")
    for needle in ("svgwriter-controls", 'data-name="size"', "id='svgwriter-build'", "role='tablist'",
                   "class='layout-auto'", "backdrop-checker", "prefers-color-scheme:dark"):
        assert needle in page, needle
    status, answer = _values(server, {"size": 40, "shape": 1})
    assert status == 200 and answer["readouts"]["size"] == "40" and not answer["error"]
    assert [view["name"] for view in answer["views"]] == ["knobs", "knobs-Spin"]
    assert 'r="40"' in answer["views"][0]["svg"] and "<animate" in answer["views"][1]["svg"]
    assert _values(server, {"size": 999}) == (400, {"error": "size: 999 is outside 10..80"})
    assert _values(server, {"nope": 1})[1] == {"error": "no control 'nope'"}
    assert _post(server.url + "values", b"{not json")[0] == 400
    assert _post(server.url + "values", b"[1]")[1] == {"error": "expected a JSON object"}
    status, answer = _values(server, {"size": 75})
    assert status == 200 and "too big on purpose" in answer["error"] and 'r="40"' in answer["views"][0]["svg"]
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(urllib.request.Request(server.url + "other", data=b"{}"))
    state = json.loads(urllib.request.urlopen(server.url + "state").read())
    assert "svgwriter-controls" in state["form"] and state["version"] == server.version


def test_values_write_no_outputs_and_build_does(server: LiveServer, root: Path) -> None:
    for size in (30, 31, 32):
        assert _values(server, {"size": size})[0] == 200
    assert _outputs(root) == []
    status, answer = _post(server.url + "build", b"")
    assert status == 200 and answer["files"] == ["knobs.svg", "knobs-Spin.svg", "knobs.png", "knobs-Spin.png"]
    assert 'width="32"' in (root / "output" / "knobs.svg").read_text(encoding="utf-8")


def test_rapid_concurrent_values_coalesce(server: LiveServer, capfd: pytest.CaptureFixture[str]) -> None:
    sizes = list(range(10, 70, 2))
    threads = [threading.Thread(target=_values, args=(server, {"size": size})) for size in sizes]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(WAIT)
    status, answer = _values(server, {"size": 66, "shape": 1})
    assert status == 200 and answer["readouts"]["size"] == "66" and 'r="66"' in answer["views"][0]["svg"]
    assert server.values == {"size": 66, "shape": "dot"}
    captured = capfd.readouterr()
    assert "Traceback" not in captured.err + captured.out


def test_disconnecting_clients_are_quiet(server: LiveServer, capfd: pytest.CaptureFixture[str]) -> None:
    host, port = server.server.server_address[:2]
    body = json.dumps({"size": 50}).encode()
    for _ in range(5):
        with socket.create_connection((host, port)) as client:
            client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00")
            client.sendall(b"POST /values HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                           b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
    for size in range(20, 30):
        try:
            _values(server, {"size": size}, timeout=0.001)
        except OSError:
            pass
    assert _values(server, {"size": 52})[1]["readouts"]["size"] == "52"
    time.sleep(0.2)
    captured = capfd.readouterr()
    assert "Traceback" not in captured.err + captured.out and "Error" not in captured.err


def test_file_save_reimports_and_builds(root: Path) -> None:
    manifest = root / "svgwriter.toml"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace("build_on_save = false", "build_on_save = true"),
                        encoding="utf-8")
    live = LiveServer(LiveProject(root), 0)
    thread = threading.Thread(target=live.serve, kwargs={"open_browser": False}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + WAIT
        while live.version == 0:
            assert time.monotonic() < deadline
            time.sleep(0.05)
        assert _values(live, {"size": 30, "shape": 1})[0] == 200 and _outputs(root) == []
        version = live.version
        (root / "main.py").write_text(MAIN.replace("size=(10, 80)", "size=(10, 40)").replace("#0ea5e9", "#f43f5e"),
                                      encoding="utf-8")
        while live.version == version or not _outputs(root):
            assert time.monotonic() < deadline
            time.sleep(0.05)
        assert live.fields["size"].max == 40 and "#f43f5e" in live.views[0].svg
        assert "#f43f5e" in (root / "output" / "knobs.svg").read_text(encoding="utf-8")
        assert 'r="30"' in live.views[0].svg
    finally:
        live.close()
        thread.join(5)


def test_preview_pages_choose_and_order(root: Path) -> None:
    manifest = root / "svgwriter.toml"
    manifest.write_text(manifest.read_text(encoding="utf-8") + 'pages = ["knobs-Spin", "knobs"]\n', encoding="utf-8")
    live = LiveServer(LiveProject(root), 0)
    try:
        live.reload()
        assert [view.name for view in live.views] == ["knobs-Spin", "knobs"]
        manifest.write_text(manifest.read_text(encoding="utf-8").replace('"knobs-Spin", ', '"cover", '),
                            encoding="utf-8")
        live.reload()
        assert "preview.pages names 'cover'" in live.error
    finally:
        live.live.close()
        live.server.server_close()


def test_preview_config(tmp_path: Path) -> None:
    project = svg.Project.new(tmp_path / "plain")
    assert project.config.preview == PreviewConfig()
    manifest = project.root / "svgwriter.toml"
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(text + '[preview]\nbackground = "#102030"\nlayout = "bottom"\nfit = "actual"\nport = 8123\n'
                        'open = false\ndebounce_ms = 40\nformats_on_build = ["SVG"]\n', encoding="utf-8")
    settings = svg.Project.load(project.root).config.preview
    assert settings == PreviewConfig(background="#102030", layout="bottom", fit="actual", port=8123, open=False,
                                     debounce_ms=40, formats_on_build=("svg",))
    for table, message in [("zoom = 2", "unknown key preview.'zoom'"), ('layout = "left"', "preview.layout is one of"),
                           ('background = "plaid"', "preview.background is one of"),
                           ("open = 1", "preview.open is true or false"),
                           ("debounce_ms = -1", "preview.debounce_ms is a whole number"),
                           ("pages = 3", "preview.pages is a list of names"),
                           ('formats_on_build = ["doc"]', "unknown format 'doc'")]:
        manifest.write_text(text + f"[preview]\n{table}\n", encoding="utf-8")
        with pytest.raises(ProjectError, match=message) as error:
            svg.Project.load(project.root)
        assert "svgwriter.toml" in str(error.value)
    manifest.unlink()
    (project.root / "pyproject.toml").write_text('[tool.svgwriter.project]\nname = "plain"\n'
                                                 '[tool.svgwriter.preview]\nfit = "actual"\n', encoding="utf-8")
    assert svg.Project.load(project.root).config.preview.fit == "actual"


def test_live_project_restores_folder_and_modules(root: Path) -> None:
    import sys

    before = Path.cwd()
    live = LiveProject(root)
    assert list(live.load()) == ["size", "shape"] and Path.cwd() == root.resolve()
    assert "main" in sys.modules
    live.close()
    assert Path.cwd() == before and "main" not in sys.modules

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.project._form import controls_form
from svgwriter.project._server import LiveServer

MAIN = '''import svgwriter as svg


@svg.widgets.controls(size=(10, 80), color=svg.widgets.Swatches(["#0ea5e9", "#f43f5e"]), label="Hi",
                      shape=["box", "dot"], round_=False, band=svg.widgets.RangeSlider(0, 10),
                      layers=svg.widgets.MultiSelect(["a", "b"]), count=svg.widgets.Number(2),
                      tint="#00ff00", pick=svg.widgets.Dropdown(list("pqrst")))
def build(doc, size=20, color="#0ea5e9", label="Hi", shape="box", round_=False, band=None, layers=(), count=2,
          tint="#00ff00", pick="p"):
    if size > 70:
        raise RuntimeError("too big on purpose")
    if shape == "box":
        doc.rect(0, 0, size, size, fill=color)
    else:
        doc.circle(size, size, size, fill=color)
'''


@pytest.fixture
def project(tmp_path: Path) -> svg.Project:
    made = svg.Project.new(tmp_path / "knobs")
    (made.root / "main.py").write_text(MAIN, encoding="utf-8")
    return svg.Project.load(made.root)


def test_project_controls_and_values(project: svg.Project) -> None:
    found = project.controls()
    assert list(found)[:3] == ["size", "color", "label"] and found["size"].initial == 20
    default = project.build(["svg"])[0].read_text(encoding="utf-8")
    assert 'width="20"' in default and "#0ea5e9" in default
    chosen = project.build(["svg"], values={"size": 33, "shape": "dot"})[0].read_text(encoding="utf-8")
    assert 'r="33"' in chosen
    with pytest.raises(ValueError):
        project.build(["svg"], values={"size": 500})


def test_form_html() -> None:
    @svg.widgets.controls(size=(0, 10), on=True, tone="#ff0000", note="x", pick=list("abcde"), seg=["a", "b"],
                          chips=["#ff0000", "#00ff00"], many=svg.widgets.MultiSelect(["a", "b"], value=["b"]),
                          band=svg.widgets.RangeSlider(0, 4), count=svg.widgets.Number(1, min=0, max=5),
                          tick=svg.widgets.Checkbox())
    def every(size=1, on=True, tone="#ff0000", note="x", pick="a", seg="b", chips="#ff0000", many=(), band=None,
              count=1, tick=False):
        return svg.Document()

    form = controls_form(svg.widgets.controls_of(every), {"size": 3})
    assert form.count("class='field'") == 11
    for needle in ("type='range' min=\"0\" max=\"10\" step=\"1\" value=\"3\"", "class='switch'", "type='color'",
                   "<select>", "<select multiple>", "data-kind=\"pair\"", "data-kind=\"indices\"",
                   "class='chip'", "type='number'", "fetch('/values'", "value=\"1\" checked=\"True\""):
        assert needle in form, needle
    assert controls_form({}, {}) == ""
    class Knob(svg.widgets.Control):
        def check(self, value):
            return value

        def _default(self):
            return 0

    with pytest.raises(TypeError, match="no preview input"):
        controls_form({"x": Knob()}, {})


def _post(url: str, body: bytes) -> tuple[int, dict]:
    request = urllib.request.Request(url + "values", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request) as answer:
            return answer.status, json.loads(answer.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_server_control_endpoint(project: svg.Project) -> None:
    root = project.root
    server = LiveServer(root, lambda values: svg.Project.load(root).build(["svg"], values=values), "knobs", 0,
                        controls=lambda: svg.Project.load(root).controls())
    thread = threading.Thread(target=server.serve, kwargs={"open_browser": False}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 20
        while server.version == 0 and time.monotonic() < deadline:
            time.sleep(0.05)
        page = urllib.request.urlopen(server.url).read().decode("utf-8")
        assert "svgwriter-controls" in page and 'data-name="size"' in page and "svgwriter-outputs" in page
        status, answer = _post(server.url, json.dumps({"size": 40, "color": 1, "shape": 1}).encode())
        assert status == 200 and answer["version"] == server.version and answer["readouts"]["size"] == "40"
        assert "knobs.svg" in answer["outputs"] and server.values["color"] == "#f43f5e"
        assert 'r="40"' in (root / "output" / "knobs.svg").read_text(encoding="utf-8")
        version = server.version
        assert _post(server.url, json.dumps({"size": 40}).encode())[0] == 200 and server.version == version + 1
        assert _post(server.url, json.dumps({"size": 999}).encode()) == (400, {"error": "size: 999 is outside 10..80"})
        assert _post(server.url, json.dumps({"nope": 1}).encode())[1] == {"error": "no control 'nope'"}
        assert _post(server.url, b"{not json")[0] == 400
        assert _post(server.url, b"[1]")[1] == {"error": "expected a JSON object"}
        status, answer = _post(server.url, json.dumps({"size": 75}).encode())
        assert status == 200 and "too big on purpose" in answer["outputs"] and "knobs.svg" in answer["outputs"]
        assert "build failed" in server.page
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(urllib.request.Request(server.url + "other", data=b"{}"))
        (root / "main.py").write_text(MAIN.replace("size=(10, 80)", "size=(10, 30)"), encoding="utf-8")
        while server.error or server.fields.get("size") is None or server.fields["size"].max != 30:
            assert time.monotonic() < deadline
            time.sleep(0.05)
        assert "size" not in server.values and server.values["shape"] == "dot"
    finally:
        server.close()
        thread.join(5)

from __future__ import annotations

import builtins
import sys
import time

import pytest

import svgwriter as svg
from svgwriter.tools.widgets import Interactive, Recorder, Slider
from svgwriter.tools.widgets._constants import SEGMENTED_WRAP


def badge(radius=10, color="#0ea5e9", label="Hi"):
    return svg.circle(radius, radius, radius, fill=color)


class TestInteract:
    def test_panel_and_state(self) -> None:
        panel = Recorder()
        view = svg.interact(badge, radius=(2, 40), color=["#0ea5e9", "#f43f5e"], backend=panel, delay=0)
        assert list(panel.controls) == ["radius", "color"] and panel.inputs == {"radius": 10, "color": "#0ea5e9"}
        assert panel.shown == 1 and len(panel.drawings) == 1 and panel.message is None
        panel.set("radius", 30)
        panel.set("color", 1)
        assert view.values == {"radius": 30, "color": "#f43f5e"}
        assert 'r="30"' in panel.drawings[-1] and "#f43f5e" in panel.drawings[-1]
        assert view.document.root[0].get("r") == 30
        assert view.code() == "badge(radius=30, color='#f43f5e')"
        assert repr(view) == "<Interactive badge(radius=30, color='#f43f5e')>"

    def test_inferred_controls_and_document_functions(self) -> None:
        @svg.widgets.controls(size=(4, 40))
        def tile(doc, size=8):
            doc.rect(0, 0, size, size)

        view = svg.interact(tile, backend=Recorder())
        assert view.values == {"size": 8} and view.document.root[0].tag == "rect"
        assert svg.interact(badge, backend=Recorder()).values == {"radius": 10, "color": "#0ea5e9", "label": "Hi"}

    def test_errors_keep_the_last_drawing(self) -> None:
        def fragile(n=1):
            if n > 5:
                raise RuntimeError("too many")
            return svg.text(str(n))

        panel = Recorder()
        view = svg.interact(fragile, n=(0, 10), backend=panel, delay=0)
        panel.set("n", 8)
        assert "too many" in panel.message and "too many" in view.error and len(panel.drawings) == 1
        assert view.document.root[0].children == ["1"]
        panel.set("n", 99)
        assert "outside" in panel.message and view.values["n"] == 8
        panel.set("n", 2)
        assert panel.message is None and view.error is None and len(panel.drawings) == 2

    def test_first_drawing_fails(self) -> None:
        view = svg.interact(lambda n=1: 1 / 0, backend=Recorder())
        with pytest.raises(RuntimeError, match="ZeroDivisionError"):
            _ = view.document
        with pytest.raises(RuntimeError, match="returned int"):
            Interactive(lambda: 3, {}, Recorder()).document  # noqa: B018

    def test_cache_and_update(self) -> None:
        calls = []

        def counted(n=1):
            calls.append(n)
            return svg.text(str(n))

        panel = Recorder()
        view = svg.interact(counted, n=(0, 9), backend=panel, delay=0)
        view.update(n=4).update(n=1).update(n=4)
        assert calls == [1, 4] and len(panel.drawings) == 4
        view.update(n=4)
        assert len(panel.drawings) == 4
        with pytest.raises(KeyError, match="no control"):
            view.update(m=1)
        with pytest.raises(ValueError):
            view.update(n=50)

    def test_debounce(self) -> None:
        calls = []

        def counted(n=1):
            calls.append(n)
            return svg.text(str(n))

        panel = Recorder()
        view = svg.interact(counted, n=(0, 9), backend=panel, delay=0.05)
        for value in range(2, 8):
            panel.set("n", value)
        deadline = time.monotonic() + 5
        while calls[-1] != 7 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert calls == [1, 7] and view.values == {"n": 7}

    def test_save(self, tmp_path) -> None:
        view = svg.interact(badge, backend=Recorder()).update(radius=12)
        target = view.save(tmp_path / "badge.svg")
        assert 'r="12"' in target.read_text(encoding="utf-8")
        view.save(tmp_path / "badge.png")
        assert (tmp_path / "badge.png").read_bytes()[:4] == b"\x89PNG"

    def test_show_again(self) -> None:
        panel = Recorder()
        view = svg.interact(badge, backend=panel)
        view._ipython_display_()
        view.show()
        assert panel.shown == 3

    def test_unknown_backend_value(self) -> None:
        with pytest.raises(TypeError, match="no parameter"):
            svg.interact(badge, size=(0, 1), backend=Recorder())
        with pytest.raises(RuntimeError, match="no panel"):
            Recorder().set("x", 1)


def test_missing_ipywidgets(monkeypatch) -> None:
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "ipywidgets":
            raise ImportError("blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "ipywidgets", raising=False)
    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ImportError, match=r"pysvgwriter\[widget\]"):
        svg.interact(badge)


def test_notebook_backend_widgets() -> None:
    pytest.importorskip("ipywidgets")
    from svgwriter.tools.widgets import _ipywidgets

    panel = _ipywidgets.NotebookBackend()
    controls = {
        "r": Slider(1, 10, units="mm").titled("r"), "n": svg.widgets.IntSlider(0, 5).titled("n"),
        "band": svg.widgets.RangeSlider(0, 10).titled("band"), "on": svg.widgets.Toggle().titled("on"),
        "tick": svg.widgets.Checkbox().titled("tick"), "pick": svg.widgets.Dropdown(list("abcde")).titled("pick"),
        "seg": svg.widgets.Segmented(list("ab")).titled("seg"), "many": svg.widgets.MultiSelect(["x", "y"]).titled("many"),
        "chip": svg.widgets.Swatches(["red", "blue"]).titled("chip"), "count": svg.widgets.Number(3).titled("count"),
        "text": svg.widgets.Text("hi").titled("text"), "color": svg.widgets.ColorPicker("#ff000080").titled("color"),
    }
    view = Interactive(lambda **kw: svg.circle(5, 5, 5), controls, panel, delay=0)
    rows = panel._box.children[2].children
    rows[0].children[1].children[0].value = 7.0
    assert rows[0].children[1].children[1].value == "7mm"
    rows[5].children[1].value = 4
    rows[7].children[1].value = (0, 1)
    rows[8].children[1].children[1].click()
    rows[3].children[1].value = True
    assert view.values["r"] == 7.0 and view.values["pick"] == "e" and view.values["many"] == ("x", "y")
    assert view.values["chip"] == "blue" and view.values["on"] is True
    assert "<svg" in panel._image.value and panel._error.value == ""
    panel.fail("bad <thing>")
    assert "bad &lt;thing&gt;" in panel._error.value
    panel.show()
    assert type(rows[6].children[1]).__name__ == "ToggleButtons"
    assert type(rows[5].children[1]).__name__ == "Dropdown"
    with pytest.raises(TypeError, match="no notebook input"):
        _ipywidgets._input(_ipywidgets._widgets(), svg.widgets.Control(), None, print)


@pytest.mark.parametrize(("count", "kind"), [(SEGMENTED_WRAP, "ToggleButtons"), (SEGMENTED_WRAP + 1, "Dropdown")])
def test_segmented_layout_by_option_count(count: int, kind: str) -> None:
    pytest.importorskip("ipywidgets")
    from svgwriter.tools.widgets import _ipywidgets

    control = svg.widgets.Segmented([str(n) for n in range(count)])
    shown = _ipywidgets._input(_ipywidgets._widgets(), control, control.initial, print)
    assert type(shown).__name__ == kind

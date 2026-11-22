from __future__ import annotations

from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.tools.project._form import controls_form

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
                   "<select aria-labelledby=\"label-pick\">", "<select multiple", "data-kind=\"pair\"", "data-kind=\"indices\"",
                   "class='chip'", "type='number'", "aria-labelledby=\"label-size\"", "role='radiogroup'",
                   "id=\"label-tick\"", "value=\"1\" checked=\"True\""):
        assert needle in form, needle
    assert controls_form({}, {}) == ""
    class Knob(svg.widgets.Control):
        def check(self, value):
            return value

        def _default(self):
            return 0

    with pytest.raises(TypeError, match="no preview input"):
        controls_form({"x": Knob()}, {})


def test_segmented_becomes_a_select_past_the_wrap_limit() -> None:
    few = svg.widgets.Segmented([str(n) for n in range(6)])
    many = svg.widgets.Segmented([str(n) for n in range(7)])
    assert "class='segmented'" in controls_form({"few": few}, {})
    form = controls_form({"many": many}, {})
    assert "<select" in form and "segmented" not in form and 'data-kind="index"' in form

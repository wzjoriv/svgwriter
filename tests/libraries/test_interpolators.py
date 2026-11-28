import subprocess
import sys
from importlib import metadata

import numpy as np
import pytest

import svgwriter as svg
from svgwriter._internal._presets import INTERPOLATORS

PLUGIN = '''
import svgwriter as svg


@svg.preset.interpolator(attribute="opacity")
def halfway(a, b, t):
    return a if t < 0.5 else b
'''


def test_builtins_are_registered_in_order():
    assert svg.preset.interpolator.list()[:8] == [
        "number", "matrix", "path", "array", "batch", "element", "sequence", "color"]
    assert svg.preset.KINDS["interpolator"] is INTERPOLATORS


def test_importing_the_library_first_keeps_builtins_built_in():
    code = ("import svgwriter.library.interpolators\nfrom svgwriter._internal._presets import INTERPOLATORS\n"
            "print(len(INTERPOLATORS.builtins), len(INTERPOLATORS.user))")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.split() == ["8", "0"]


def test_a_kind_interpolator_wins_over_the_builtins():
    class Weight(int):
        pass

    @svg.preset.interpolator(kind=Weight)
    def weight(a, b, t):
        return Weight(round(a + (b - a) * t, -2))

    try:
        assert svg.interpolate(Weight(400), Weight(700), 0.5) == 600
    finally:
        svg.preset.interpolator.unregister("weight")
    assert svg.interpolate(Weight(400), Weight(700), 0.5) == 550


def test_predicate_kinds():
    @svg.preset.interpolator(kind=lambda value: isinstance(value, str) and value.isalpha(), name="word")
    def word(a, b, t):
        return a if t < 0.5 else b

    try:
        assert svg.interpolate("thin", "bold", 0.7) == "bold"
    finally:
        svg.preset.interpolator.unregister("word")


def test_an_attribute_interpolator_changes_a_tween():
    a, b = svg.circle(0, 0, 2, stroke_width=1), svg.circle(10, 0, 4, stroke_width=4)
    assert svg.interpolate(a, b, 0.4).get("stroke-width") == pytest.approx(2.2)

    @svg.preset.interpolator(attribute="stroke_width")
    def stepped(first, second, t):
        return round(first + (second - first) * t)

    try:
        mixed = svg.interpolate(a, b, 0.4)
        assert mixed.get("stroke-width") == 2 and mixed.r == pytest.approx(2.8)
        morph = svg.interpolate(a, svg.rect(0, 0, 5, 5, stroke_width=4), 0.4)
        assert morph.tag == "path" and morph.get("stroke-width") == 2
    finally:
        svg.preset.interpolator.unregister("stepped")


def test_an_attribute_interpolator_reaches_batch_columns():
    xs = np.arange(3.0)
    a = svg.batch.circles(xs, xs, xs + 1, stroke_width=[1.0, 1.0, 1.0])
    b = svg.batch.circles(xs, xs, xs + 2, stroke_width=[4.0, 4.0, 4.0])

    @svg.preset.interpolator(attribute="stroke-width")
    def stepped(first, second, t):
        return round(first + (second - first) * t)

    try:
        items = svg.interpolate(a, b, 0.4).items
        assert [item.get("stroke-width") for item in items] == [2, 2, 2]
        assert items[0].r == pytest.approx(1.4)
    finally:
        svg.preset.interpolator.unregister("stepped")


def test_replacing_a_builtin_and_restoring_it():
    @svg.preset.interpolator(kind=svg.Color, name="color", replace=True)
    def first(a, b, t):
        return a

    try:
        assert svg.interpolate(svg.Color.parse("red"), svg.Color.parse("blue"), 0.9).hex == "#ff0000"
    finally:
        svg.preset.interpolator.unregister("color")
    assert svg.interpolate("red", "blue", 0.5).hex == "#800080"


def test_registering_needs_a_kind_or_attribute():
    with pytest.raises(TypeError, match="kind="):
        svg.preset.interpolator(lambda a, b, t: a)
    with pytest.raises(ValueError, match="already registered"):
        svg.preset.interpolator(lambda a, b, t: a, kind=int, name="number")


def test_plugins_load_from_entry_points(monkeypatch, tmp_path):
    (tmp_path / "svgwriter_halfway.py").write_text(PLUGIN, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    point = metadata.EntryPoint("halfway", "svgwriter_halfway:halfway", INTERPOLATORS.group)
    monkeypatch.setattr(metadata, "entry_points", lambda group: [point] if group == INTERPOLATORS.group else [])
    monkeypatch.setattr(INTERPOLATORS, "_plugins_loaded", False)
    monkeypatch.setattr(INTERPOLATORS, "_rules", None)
    state = INTERPOLATORS.state()
    try:
        a, b = svg.rect(0, 0, 4, 4, opacity=0.2), svg.rect(0, 0, 4, 4, opacity=0.8)
        assert svg.interpolate(a, b, 0.4).get("opacity") == 0.2
        assert INTERPOLATORS.group == "svgwriter.interpolator" and "halfway" in INTERPOLATORS.list()
    finally:
        INTERPOLATORS.restore(state)
    assert svg.interpolate(a, b, 0.5).get("opacity") == pytest.approx(0.5)


def test_color_overshoot_is_clamped() -> None:
    assert svg.interpolate("red", "blue", -0.3).hex == "#ff0000"
    assert svg.interpolate("red", "blue", 1.3).hex == "#0000ff"

import numpy as np
import pytest

import svgwriter as svg
from svgwriter._internal._easing import spline_progress, split_spline

TIMES = [i / 20 for i in range(21)]


def _bounce(t: float) -> float:
    if t < 1 / 2.75:
        return 7.5625 * t * t
    if t < 2 / 2.75:
        return 7.5625 * (t - 1.5 / 2.75) ** 2 + 0.75
    if t < 2.5 / 2.75:
        return 7.5625 * (t - 2.25 / 2.75) ** 2 + 0.9375
    return 7.5625 * (t - 2.625 / 2.75) ** 2 + 0.984375


def _box(**animate):
    doc = svg.Document(100, 40)
    box = doc.rect(0, 0, 10, 10)
    box.append(svg.Animate(attribute_name="x", dur=1, fill="freeze", **animate))
    return doc


def _x(doc, t):
    return float(doc.at(t)[0].get("x"))


@pytest.mark.parametrize("name", ["ease", "ease-in", "ease-out", "ease-in-out"])
def test_named_curves_have_exact_endpoints_and_stay_monotone(name):
    curve = svg.Ease(name)
    values = [curve(t) for t in TIMES]
    assert values[0] == 0 and values[-1] == 1
    assert all(b >= a for a, b in zip(values, values[1:], strict=False))


def test_curve_shapes():
    assert svg.Ease("ease-in")(0.5) < 0.5 < svg.Ease("ease-out")(0.5)
    assert svg.Ease("ease-in-out")(0.5) == pytest.approx(0.5)
    assert svg.Ease("linear")(0.3) == pytest.approx(0.3)
    assert svg.Ease((0.42, 0, 1, 1))(0.5) == pytest.approx(svg.Ease("ease-in")(0.5))
    assert svg.Ease(svg.Ease("ease-out"))(0.2) == svg.Ease("ease-out")(0.2)


def test_spline_progress_solves_x_for_the_parameter():
    spline = (0.25, 0.1, 0.25, 1.0)
    for s in np.linspace(0, 1, 11):
        x = 3 * (1 - s) ** 2 * s * 0.25 + 3 * (1 - s) * s * s * 0.25 + s**3
        y = 3 * (1 - s) ** 2 * s * 0.1 + 3 * (1 - s) * s * s * 1.0 + s**3
        assert spline_progress(spline, x) == pytest.approx(y, abs=1e-7)


def test_split_spline_whole_range_is_identity():
    assert split_spline((0.42, 0, 0.58, 1), 0, 1) == (0.42, 0, 0.58, 1)


@pytest.mark.parametrize(("curve", "expected"), [
    ("step-end", [0, 0, 0, 1]), ("step-start", [1, 1, 1, 1]),
    (("steps", 4), [0, 0.25, 0.5, 1]), (("steps", 4, "start"), [0.25, 0.5, 0.75, 1]),
])
def test_steps(curve, expected):
    assert [svg.Ease(curve)(t) for t in (0, 0.3, 0.6, 1)] == expected


@pytest.mark.parametrize("bad", ["bouncy", (1.5, 0, 0.5, 1), ("steps", 0), ("steps", 2, "middle"), 3])
def test_bad_curves_raise(bad):
    with pytest.raises((ValueError, TypeError)):
        svg.Ease(bad)


def test_time_of_inverts_the_curve():
    for curve in ("ease-in", (0.2, 0.8, 0.3, 0.9), lambda t: t**3):
        ease = svg.Ease(curve)
        for p in (0.1, 0.5, 0.9):
            assert ease(ease.time_of(p)) == pytest.approx(p, abs=1e-6)
    assert svg.Ease(("steps", 4)).time_of(0.5) == 0.5


def test_from_to_writes_one_spline():
    animate = svg.Animate(attribute_name="x", from_=0, to=10, dur=1, ease="ease-out")
    assert (animate.get("calcMode"), animate.get("keyTimes"), animate.get("keySplines")) == (
        "spline", "0;1", "0 0 0.58 1")


def test_linear_ease_changes_nothing():
    assert str(svg.Animate(attribute_name="x", from_=0, to=1, ease="linear")) == str(
        svg.Animate(attribute_name="x", from_=0, to=1))


@pytest.mark.parametrize("ease", ["ease-in", "ease", (0.1, 0.7, 0.2, 1.0)])
def test_whole_timeline_spline_over_several_values_matches_the_curve(ease):
    stops, keys = [0, 30, 40, 100], [0, 1 / 3, 2 / 3, 1]
    doc = _box(values=stops, ease=ease)
    assert len(doc[0].children[0].get("keySplines").split(";")) == 3
    curve = svg.Ease(ease)
    for t in TIMES:
        assert _x(doc, t) == pytest.approx(np.interp(curve(t), keys, stops), abs=1e-3)


@pytest.mark.parametrize("ease", [_bounce, (0.3, -0.5, 0.7, 1.5), lambda t: t * t])
def test_sampled_curves_match_the_function(ease):
    doc = _box(from_=0, to=100, ease=ease)
    count = len(doc[0].children[0].get("keyTimes").split(";")) - 1
    assert 24 <= count <= 60 and doc[0].children[0].get("calcMode") == "linear"
    curve = svg.Ease(ease)
    for t in (0, 0.25, 0.5, 1):
        assert _x(doc, t) == pytest.approx(100 * curve(t), abs=0.5)


def test_sample_count_grows_with_bending():
    def count(ease):
        return len(svg.Animate(attribute_name="x", from_=0, to=1, ease=ease).get("keyTimes").split(";")) - 1

    assert count(lambda t: t) == 24 < count(_bounce) <= 60


def test_overshoot_extrapolates_numbers():
    doc = _box(from_=0, to=100, ease=lambda t: t + np.sin(np.pi * t) * 0.3)
    assert _x(doc, 0.5) == pytest.approx(80, abs=0.5)


def test_steps_write_discrete_values():
    animate = svg.Animate(attribute_name="x", from_=0, to=100, ease=("steps", 4), dur=1)
    assert (animate.get("calcMode"), animate.get("values"), animate.get("from")) == (
        "discrete", "0;25;50;75;100", None)
    doc = _box(from_=0, to=100, ease=("steps", 4))
    assert [_x(doc, t) for t in (0.1, 0.3, 0.99, 1.0)] == [0, 25, 75, 100]


def test_discrete_animation_keeps_values_and_moves_times():
    animate = svg.Animate(attribute_name="x", values="1;0;1", calc_mode="discrete", ease="ease-in")
    times = [float(t) for t in animate.get("keyTimes").split(";")]
    assert animate.get("values") == "1;0;1" and times[0] == 0 and times[1] > 1 / 3


def test_ease_conflicts_with_paced_or_spline_and_sampling_needs_a_start():
    with pytest.raises(ValueError, match="calcMode"):
        svg.Animate(attribute_name="x", values="0;1", calc_mode="paced", ease="ease-in")
    with pytest.raises(ValueError, match="from_"):
        svg.Animate(attribute_name="x", to=1, ease=lambda t: t)
    assert svg.Animate(attribute_name="x", to=1, ease="ease-in").get("keySplines") == "0.42 0 1 1"


def test_colors_and_transforms_take_ease():
    doc = svg.Document(10, 10)
    box = doc.rect(0, 0, 5, 5, fill="black")
    box.append(svg.Animate(attribute_name="fill", from_="black", to="white", dur=1, ease=_bounce))
    box.append(svg.AnimateTransform("translate", from_="0 0", to="10 0", dur=1, ease="ease-in"))
    frame = doc.at(0.5)[0]
    assert frame.get("fill") != "#000000"
    assert frame.t.e == pytest.approx(10 * svg.Ease("ease-in")(0.5), abs=1e-4)


def test_motion_along_a_path_uses_key_points():
    motion = svg.AnimateMotion(path="M0 0L100 0", dur=1, ease="ease-in")
    assert (motion.get("keyPoints"), motion.get("keySplines")) == ("0;1", "0.42 0 1 1")
    doc = svg.Document(100, 10)
    dot = doc.circle(0, 0, 2)
    dot.animate.follow("M0 0L100 0", ease=_bounce, rotate=False)
    assert doc.at(0.5)[0].t.e == pytest.approx(100 * _bounce(0.5), abs=1e-2)


def test_paced_spaces_values_by_distance():
    doc = _box(values="0;10;100", calc_mode="paced")
    assert [_x(doc, t) for t in (0.05, 0.1, 0.55)] == pytest.approx([5, 10, 55])
    colors = svg.Document(10, 10)
    swatch = colors.rect(0, 0, 5, 5)
    swatch.append(svg.Animate(attribute_name="fill", values="#000000;#000000;#ffffff", calc_mode="paced", dur=1))
    assert colors.at(0.5)[0].get("fill") == "#808080"


def test_spline_mode_written_by_hand_is_evaluated():
    doc = _box(values="0;100", calc_mode="spline", key_times="0;1", key_splines=[(0.42, 0, 1, 1)])
    assert _x(doc, 0) == 0 and _x(doc, 1) == 100
    assert _x(doc, 0.5) == pytest.approx(100 * svg.Ease("ease-in")(0.5), abs=1e-4) and _x(doc, 0.5) < 50


@pytest.mark.parametrize(("preset", "args"), [
    ("tween", ("x", 0, 10)), ("fade_in", ()), ("fade_out", ()), ("grow", ()), ("shrink", ()), ("pulse", ()),
    ("spin", ()), ("slide_in", ()), ("move_to", (50, 5)), ("shake", ()), ("bounce", ()), ("blink", ()),
    ("color_cycle", (["red", "blue"],)), ("wipe", ()), ("draw", ()), ("create", ()), ("uncreate", ()),
    ("write", ()), ("follow", ("M0 0L10 10",)), ("morph", (svg.circle(5, 5, 5),)),
])
def test_every_preset_takes_ease(preset, args):
    doc = svg.Document(100, 100)
    box = doc.add(svg.Path("M0 0H10V10H0Z", fill="red", stroke="black"))
    getattr(box.animate, preset)(*args, ease="ease-in-out")
    animations = list(doc.root.find_all(svg.AnimationElement))
    assert any(a.get("calcMode") in ("spline", "discrete") for a in animations)


def test_typewriter_and_stagger_follow_the_curve():
    text = svg.Text("abcd", x=0, y=10)
    text.animate.typewriter(1, ease="ease-in")
    begins = [float(str(span.find(svg.Set).get("begin")).rstrip("s")) for span in text.children]
    assert begins[0] == 0 and begins[2] == pytest.approx(svg.Ease("ease-in").time_of(0.5), abs=1e-6)
    group = svg.Group(svg.rect(0, 0, 1, 1), svg.rect(2, 0, 1, 1))
    group.animate.stagger("fade_in", ease="ease-out")
    assert all(child.children[0].get("keySplines") == "0 0 0.58 1" for child in group)


def test_write_spaces_characters_along_the_curve():
    def starts(ease):
        text = svg.Text("abcde", x=0, y=10)
        text.animate.write(2, ease=ease)
        return [float(str(span.children[-2].get("begin")).rstrip("s")) for span in text.children]

    linear, eased = starts(None), starts("ease-in")
    assert linear[0] == eased[0] == 0 and linear[-1] == pytest.approx(eased[-1])
    assert eased[2] > linear[2]

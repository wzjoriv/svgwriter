import pytest
from PIL import Image

import svgwriter as svg


def _bounds(doc, time=5.0):
    box = doc.at(time).root.get_element_by_id("a").bounds()
    return tuple(round(v, 3) for v in box)


def _animated(preset, base=lambda e: e):
    doc = svg.Document(width=200, height=200)
    preset(doc.add(base(svg.rect(40, 50, 40, 20, id="a"))).animate)
    return doc


BASES = [lambda e: e, lambda e: e.rotate(20).translate(5, 7), lambda e: e.scale(2).translate(-10, 0)]


@pytest.mark.parametrize("base", BASES)
@pytest.mark.parametrize(("preset", "static"), [
    (lambda m: m.rotate(30), lambda e: e.rotate(30)),
    (lambda m: m.rotate(-45, about=(0, 0)), lambda e: e.rotate(-45, about=(0, 0))),
    (lambda m: m.rotate(30).rotate(30, begin=1), lambda e: e.rotate(60)),
    (lambda m: m.scale(2), lambda e: e.scale(2)),
    (lambda m: m.move_by(10, -5), lambda e: e.translate(10, -5)),
    (lambda m: m.move_to(100, 120), lambda e: e.place(100, 120)),
    (lambda m: m.spin(turns=0.25), lambda e: e.rotate(90)),
])
def test_end_state_matches_the_static_transform(base, preset, static):
    expected = static(base(svg.rect(40, 50, 40, 20))).bounds()
    assert _bounds(_animated(preset, base)) == tuple(round(v, 3) for v in expected)


def test_skew_and_uneven_scale_match_the_static_ones_and_skew_needs_an_angle():
    for preset, static in [(lambda m: m.skew(20, 10), lambda e: e.skew(20, 10)),
                           (lambda m: m.scale((1.5, 0.5), about=(10, 10)), lambda e: e.scale(1.5, 0.5, about=(10, 10)))]:
        expected = static(svg.rect(40, 50, 40, 20)).bounds()
        assert _bounds(_animated(preset)) == tuple(round(v, 3) for v in expected)
    with pytest.raises(ValueError, match="skew needs an angle"):
        svg.rect(0, 0, 1, 1).animate.skew()


def test_presets_pivot_on_a_set_anchor_and_local_points():
    rect = svg.rect(0, 0, 40, 20)
    rect.anchor = (0, 0)
    assert rect.animate.rotate(90).element.children[0].get("to") == "90 0 0"
    moved = svg.rect(0, 0, 10, 10).translate(100, 0)
    assert moved.animate.rotate(90, about=(100, 0)).element.children[0].get("to") == "90 0 0"
    assert svg.rect(0, 0, 10, 10).animate.rotate(90, about=(3, 4), local=True).element.children[0].get("to") == "90 3 4"
    assert svg.rect(0, 0, 10, 10).rotate(90).animate.move_by(10, 0, local=True).element.children[0].get("to") == "10 0"


def test_halfway_and_timing_keywords():
    doc = _animated(lambda m: m.move_by(100, 0, 2, begin=1, ease="linear"))
    assert _bounds(doc, 0.5)[0] == 40 and _bounds(doc, 2.0)[0] == 90 and _bounds(doc, 9)[0] == 140
    loose = _animated(lambda m: m.scale(3, 1, freeze=False))
    assert _bounds(loose, 5)[2] == 40
    looping = svg.rect(0, 0, 1, 1).animate.rotate(10, repeat="indefinite").element.children[0]
    assert looping.get("repeatCount") == "indefinite" and looping.get("additive") == "sum"


def test_transform_presets_play_in_gif_frames(tmp_path):
    doc = svg.Document(width=60, height=60)
    doc.add(svg.rect(20, 25, 20, 10, fill="teal")).animate.rotate(90).scale(1.5, begin=1).skew(x=20, begin=2)
    target = tmp_path / "presets.gif"
    doc.save(target)
    with Image.open(target) as image:
        frames = []
        for index in range(image.n_frames):
            image.seek(index)
            frames.append(image.convert("RGB").tobytes())
    assert len(frames) > 1 and len(set(frames)) > 1

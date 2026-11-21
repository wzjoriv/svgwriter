"""Interpolating and morphing themed elements; SMIL and behaviours playing together."""

import pytest

import svgwriter as svg

SPEED = 20
FADE = 1.0


def test_interpolate_between_themed_elements_switches_roles_halfway():
    a = svg.rect(0, 0, 10, 10).as_role("shape")
    b = svg.rect(20, 0, 20, 10).as_role("accent")
    early, late = svg.interpolate(a, b, 0.25), svg.interpolate(a, b, 0.75)
    assert (early.classes, late.classes) == (["role-shape"], ["role-accent"])
    assert early.get("width") == pytest.approx(12.5)
    doc = svg.Document(50, 20, theme="dark")
    doc += late
    assert ".role-accent" in doc.to_string()


def test_morph_between_themed_shapes_keeps_the_role():
    doc = svg.Document(60, 20, theme="dark")
    square = doc.add(svg.rect(0, 0, 10, 10).as_role("shape").to_path())
    start = str(square.get("d"))
    square.animate.morph(svg.circle(30, 5, 5).to_path(), 2)
    middle = doc.at(1.0).root.find(svg.Path)
    assert middle.classes == ["role-shape"] and str(middle.get("d")) != start
    assert ".role-shape" in doc.at(1.0).to_string()


def test_behaviours_and_smil_play_together():
    @svg.preset.behavior
    def integration_drift(element: svg.Element, seconds: float, *, speed: float = SPEED) -> None:
        element.t = element.home.t
        element.translate(speed * seconds, 0)

    class Both(svg.Scene):
        width, height, fps, duration = 100, 40, 4, 2.0

        def build(self, doc: svg.Document) -> None:
            self.box = doc.rect(0, 10, 10, 10).as_role("shape")
            self.box.animate.fade_in(FADE)
            self.box.animate.integration_drift()

    try:
        baked = Both().bake()
        frame = baked.at(0.5)
        box = frame.root.find(svg.Rect)
        assert float(box.get("opacity")) == pytest.approx(0.5)
        assert box.bounds().x == pytest.approx(SPEED * 0.5)
        assert ".role-shape" in frame.to_string()
    finally:
        svg.preset.behavior.unregister("integration_drift")

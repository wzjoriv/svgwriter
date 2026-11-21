from __future__ import annotations

import math

import pytest

import svgwriter as svg
from svgwriter.video.behaviors import breathe, hover, wiggle


def sway(element: svg.Element, seconds: float, *, angle: float = 10.0) -> None:
    element.t = element.home.t
    element.rotate(angle * math.sin(math.tau * seconds))


@pytest.fixture
def registered():
    assert svg.preset.behavior(sway) is sway
    yield "sway"
    svg.preset.unregister("behavior", "sway")


class Stage(svg.Scene):
    width, height, fps, duration = 40, 40, 4, 1.0

    def build(self, doc: svg.Document) -> None:
        self.box = doc.rect(10, 10, 20, 20)


class TestRegistry:
    def test_builtins_are_listed(self) -> None:
        assert {"wiggle", "hover", "breathe"} <= set(svg.preset.list("behavior"))
        assert svg.preset.get("behavior", "wiggle") is wiggle

    def test_named_and_replace(self) -> None:
        @svg.preset.behavior(name="rock")
        def rocking(element: svg.Element, seconds: float, *, angle: float = 1.0) -> None:
            pass

        try:
            with pytest.raises(ValueError, match="already registered"):
                svg.preset.behavior(name="rock")(rocking)
            assert svg.preset.behavior(name="rock", replace=True)(sway) is sway
            assert svg.preset.get("behavior", "rock") is sway
        finally:
            svg.preset.unregister("behavior", "rock")

    def test_builtin_needs_replace(self) -> None:
        with pytest.raises(ValueError, match=r"built in"):
            svg.preset.behavior(name="wiggle")(sway)
        with pytest.raises(KeyError, match="built in"):
            svg.preset.unregister("behavior", "wiggle")

    @pytest.mark.parametrize("function", [
        lambda element: None,
        lambda element, *, seconds=0: None,
        lambda element, seconds, size: None,
        lambda element, seconds, *, size: None,
    ])
    def test_signature_is_checked(self, function) -> None:
        with pytest.raises(TypeError, match="def bad"):
            svg.preset.behavior(name="bad")(function)
        assert "bad" not in svg.preset.list("behavior")

    def test_names_shared_with_animations(self) -> None:
        with pytest.raises(ValueError, match="animation preset"):
            svg.preset.behavior(name="fade_in")(sway)
        with pytest.raises(ValueError, match="is a behavior"):
            svg.preset.animation(name="wiggle")(lambda motion: motion)
        with pytest.raises(ValueError, match="identifiers"):
            svg.preset.behavior(name="_hidden")(sway)


class TestAttach:
    def test_typed_attach_records_home_once(self) -> None:
        scene = Stage()
        assert scene.attach(scene.box, sway, angle=5) is scene.box
        home = scene.box.home
        scene.attach(scene.box, hover)
        assert scene.box.home is home and home is not scene.box and home.get("x") == 10

    def test_run_in_order_before_update(self) -> None:
        calls: list[tuple[str, float]] = []

        class Logged(Stage):
            def build(self, doc: svg.Document) -> None:
                super().build(doc)
                self.attach(self.box, lambda el, t: calls.append(("first", t)))
                self.attach(self.box, lambda el, t, *, tag="second": calls.append((tag, t)), tag="other")

            def update(self, seconds: float) -> None:
                calls.append(("update", seconds))

        list(Logged().frames(fps=2))
        assert calls == [("first", 0.0), ("other", 0.0), ("update", 0.0),
                         ("first", 0.5), ("other", 0.5), ("update", 0.5)]

    def test_by_name_in_a_scene(self, registered: str) -> None:
        scene = Stage()
        assert scene.box.animate.sway(angle=30).element is scene.box
        scene.render(0.25)
        assert scene.box.t.decompose()[2] == pytest.approx(30)
        assert "sway" in dir(scene.box.animate)

    def test_by_name_in_build(self) -> None:
        class Built(Stage):
            def build(self, doc: svg.Document) -> None:
                super().build(doc)
                self.box.animate.hover(height=6)

        scene = Built()
        scene.render(0.5)
        assert scene.box.t.f == pytest.approx(-6)

    def test_by_name_outside_a_scene(self) -> None:
        with pytest.raises(ValueError, match="runs in a scene"):
            svg.rect(0, 0, 4, 4).animate.wiggle()
        with pytest.raises(ValueError, match="runs in a scene"):
            svg.Document(10, 10).rect(0, 0, 4, 4).animate.wiggle()

    def test_unknown_name_suggests(self) -> None:
        with pytest.raises(AttributeError, match="'wiggle'"):
            svg.rect().animate.wigle()

    def test_home_needs_a_behavior(self) -> None:
        with pytest.raises(ValueError, match="no home yet"):
            _ = svg.rect().home


class TestBuiltins:
    def test_no_drift(self) -> None:
        scene = Stage()
        scene.attach(scene.box, wiggle, angle=20, period=1)
        scene.attach(scene.box, breathe, amount=0.5, period=1)
        for seconds in (0.3, 0.7, 0.3):
            scene.render(seconds)
        first = scene.box.t
        scene.render(0.3)
        assert scene.box.t.isclose(first)
        scene.render(0.0)
        assert scene.box.t.is_identity

    def test_turns_about_the_centre(self) -> None:
        scene = Stage()
        scene.attach(scene.box, wiggle, angle=90, period=4)
        scene.render(1.0)
        assert scene.box.t.apply(20, 20).x == pytest.approx(20)
        assert scene.box.t.decompose()[2] == pytest.approx(90)

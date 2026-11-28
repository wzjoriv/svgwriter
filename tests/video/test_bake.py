from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.motion.video import resolve_renderer
from svgwriter.motion.video.behaviors import breathe, wiggle

PIXEL_TOLERANCE = 0.002


def scene_of(build: Callable[[svg.Scene, svg.Document], None],
             update: Callable[[svg.Scene, float], None] | None = None, *, duration: float = 1.0,
             fps: float = 10) -> svg.Scene:
    namespace: dict[str, object] = {"width": 100, "height": 60, "fps": fps, "duration": duration, "build": build}
    if update is not None:
        namespace["update"] = update
    return type("Made", (svg.Scene,), namespace)()


def smil(element: svg.Element) -> list[svg.Element]:
    return [child for child in element.children if isinstance(child, svg.Element) and child.category.name ==
            "ANIMATION"]


def baked_quietly(scene: svg.Scene, **options: object) -> svg.Document:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return scene.bake(**options)  # type: ignore[arg-type]


def mismatch(scene: svg.Scene, baked: svg.Document, seconds: float) -> float:
    """Mean channel difference (0..1) between the Python-driven frame and the baked SVG's frame."""
    draw = resolve_renderer("skia")
    scene._advance(scene.document, seconds)
    python = np.asarray(draw(scene.document, seconds), dtype=float)
    smil_frame = np.asarray(draw(baked, seconds), dtype=float)
    return float(np.abs(python - smil_frame).mean() / 255)


class TestChannels:
    def test_number_straight_run_keeps_two_keyframes(self) -> None:
        scene = scene_of(lambda self, doc: setattr(self, "box", doc.rect(0, 5, 10, 10)),
                         lambda self, t: setattr(self.box, "x", 80 * t))
        baked = baked_quietly(scene)
        (animate,) = smil(baked[0])
        assert (animate.get("attributeName"), animate.get("values"), animate.get("keyTimes")) == ("x", "0;80", "0;1")
        assert baked.at(0.25)[0].get("x") == "20"

    def test_tolerance_simplifies_curves(self) -> None:
        scene = scene_of(lambda self, doc: setattr(self, "dot", doc.circle(50, 30, 5)),
                         lambda self, t: setattr(self.dot, "cy", 30 + 20 * math.sin(math.tau * t)), fps=60)
        fine = smil(baked_quietly(scene)[0])[0].get("values").count(";")
        coarse = smil(baked_quietly(scene, tolerance=2.0)[0])[0].get("values").count(";")
        assert coarse < fine <= 60
        baked = baked_quietly(scene)
        for seconds in (0.1, 0.35, 0.8):
            scene._advance(scene.document, seconds)
            assert float(baked.at(seconds)[0].get("cy")) == pytest.approx(float(scene.document[0].cy), abs=0.011)

    def test_colors_interpolate(self) -> None:
        scene = scene_of(lambda self, doc: setattr(self, "box", doc.rect(0, 0, 10, 10, fill="red")),
                         lambda self, t: setattr(self.box, "fill", svg.Color(1 - t, 0, t)))
        (animate,) = smil(baked_quietly(scene)[0])
        assert animate.get("values") == "#ff0000;#0000ff"

    def test_path_interpolates_while_commands_match(self) -> None:
        def update(self: svg.Scene, t: float) -> None:
            self.line.d = f"M0 0 L10 {10 + 20 * t:g}" if t < 0.5 else f"M0 0 Q5 5 10 {10 + 20 * t:g}"

        scene = scene_of(lambda self, doc: setattr(self, "line", doc.path("M0 0 L10 10", stroke="black")), update)
        first, second = smil(baked_quietly(scene)[0])
        assert (first.get("begin"), first.get("dur"), first.get("values")) == ("0s", "0.4s", "M0 0 L10 10;M0 0 L10 18")
        assert second.get("begin") == "0.5s" and second.get("values").startswith("M0 0 Q5 5 10 20")

    def test_class_switches_with_sets(self) -> None:
        def update(self: svg.Scene, t: float) -> None:
            self.box.set("class", "on" if t >= 0.5 else None)

        scene = scene_of(lambda self, doc: setattr(self, "box", doc.rect(0, 0, 10, 10)), update)
        (switch,) = smil(baked_quietly(scene)[0])
        assert (switch.tag, switch.get("to"), switch.get("begin")) == ("set", "on", "0.5s")

    def test_style_property_moves_to_an_attribute(self) -> None:
        scene = scene_of(lambda self, doc: setattr(self, "box", doc.rect(0, 0, 10, 10, style="stroke:red;stroke-width:1")),
                         lambda self, t: self.box.set("style", f"stroke:red;stroke-width:{1 + 4 * t:g}"))
        box = baked_quietly(scene)[0]
        assert str(box.get("style")) == "stroke:red" and box.get("stroke-width") == "1"
        assert baked_quietly(scene).at(1.0)[0].get("stroke-width") == "5"

    def test_text_becomes_one_copy_per_value(self) -> None:
        def update(self: svg.Scene, t: float) -> None:
            self.label.children[0] = str(int(t * 2))

        scene = scene_of(lambda self, doc: setattr(self, "label", doc.text("0", x=5, y=20, id="count")), update)
        baked = baked_quietly(scene)
        assert [text.children[-1] for text in baked] == ["0", "1", "2"]
        assert [text.id for text in baked] == ["count", None, None]
        shown = [[text.get("visibility") for text in baked.at(seconds)] for seconds in (0.2, 0.6, 1.0)]
        assert shown == [[None, "hidden", "hidden"], ["hidden", "visible", "hidden"], ["hidden", "hidden", "visible"]]


class TestElementsAndTransforms:
    def test_added_and_removed_elements(self) -> None:
        def update(self: svg.Scene, t: float) -> None:
            inside = 0.3 <= t < 0.7
            if inside and self.extra is None:
                self.extra = self.document.circle(5, 5, 2, fill="green")
            elif not inside and self.extra is not None:
                self.document.root.remove(self.extra)
                self.extra = None

        scene = scene_of(lambda self, doc: (doc.rect(0, 0, 4, 4), setattr(self, "extra", None)), update)
        baked = baked_quietly(scene)
        circle = baked[1]
        assert circle.tag == "circle" and circle.get("visibility") == "hidden"
        assert [(s.get("to"), s.get("begin")) for s in smil(circle)] == [("visible", "0.3s"), ("hidden", "0.7s")]
        assert [baked.at(seconds)[1].get("visibility") for seconds in (0.0, 0.5, 0.9)] == ["hidden", "visible",
                                                                                            "hidden"]

    def test_turning_about_the_centre_is_one_rotation(self) -> None:
        def build(self: svg.Scene, doc: svg.Document) -> None:
            self.attach(doc.rect(40, 20, 20, 20), wiggle, angle=30, period=1)

        animations = smil(baked_quietly(scene_of(build))[0])
        assert [a.get("type") for a in animations] == ["translate", "rotate", "translate"]
        assert animations[0].get("values") == "50 30;50 30" and animations[-1].get("values") == "-50 -30;-50 -30"
        assert all(a.get("additive") == "sum" for a in animations)

    def test_growing_from_nothing_replaces_the_transform(self) -> None:
        def update(self: svg.Scene, t: float) -> None:
            self.dot.matrix = None
            self.dot.scale(t)

        scene = scene_of(lambda self, doc: setattr(self, "dot", doc.circle(50, 30, 10)), update)
        animations = smil(baked_quietly(scene)[0])
        assert animations[0].get("type") == "translate" and animations[0].get("additive") is None
        assert [a.get("type") for a in animations[1:]] == ["translate", "scale", "translate"]
        assert mismatch(scene, baked_quietly(scene), 0.45) < PIXEL_TOLERANCE

    def test_existing_smil_is_kept_and_plays_on_top(self) -> None:
        def build(self: svg.Scene, doc: svg.Document) -> None:
            self.box = doc.rect(10, 10, 20, 20, fill="teal")
            self.box.animate.fade_in(0.5).spin(1)

        scene = scene_of(build, lambda self, t: setattr(self.box, "x", 10 + 60 * t))
        animations = smil(baked_quietly(scene)[0])
        assert [a.tag for a in animations] == ["animate", "animate", "animateTransform"]
        assert animations[0].get("attributeName") == "x"
        for seconds in (0.25, 0.6, 0.95):
            assert mismatch(scene, baked_quietly(scene), seconds) < PIXEL_TOLERANCE

    def test_same_attribute_as_smil_switches_from_the_start(self) -> None:
        def build(self: svg.Scene, doc: svg.Document) -> None:
            self.box = doc.rect(0, 0, 10, 10)
            self.box.append(svg.Set(attribute_name="class", to="lit", begin=0.8))

        scene = scene_of(build, lambda self, t: self.box.set("class", "a" if t < 0.5 else "b"))
        animate = smil(baked_quietly(scene)[0])[0]
        assert (animate.get("calcMode"), animate.get("values"), animate.get("keyTimes")) == ("discrete", "a;b",
                                                                                            "0;0.5")


class TestScene:
    def test_without_python_motion_the_copy_is_unchanged(self) -> None:
        scene = svg.Scene(svg.Document(10, 10))
        scene.document.rect(0, 0, 2, 2).animate.fade_in(1)
        baked = scene.bake()
        assert baked is not scene.document and str(baked) == str(scene.document)

    def test_needs_a_duration(self) -> None:
        with pytest.raises(ValueError, match="duration"):
            scene_of(lambda self, doc: None, lambda self, t: None, duration=None).bake()  # type: ignore[arg-type]

    def test_one_warning_lists_what_cannot_be_expressed(self) -> None:
        def update(self: svg.Scene, t: float) -> None:
            self.box.id = f"box{int(t * 2)}"
            target = self.right if t >= 0.5 else self.left
            if self.dot.parent is not target:
                self.dot.parent.remove(self.dot)
                target.append(self.dot)

        def build(self: svg.Scene, doc: svg.Document) -> None:
            self.box = doc.rect(0, 0, 4, 4)
            self.left, self.right = doc.add(svg.Group()), doc.add(svg.Group())
            self.dot = self.left.add(svg.circle(1, 1, 1))

        with pytest.warns(UserWarning, match="cannot express") as caught:
            scene_of(build, update).bake()
        assert len(caught) == 1
        assert "<rect#box0> id changed" in str(caught[0].message)
        assert "<circle> moved to another parent" in str(caught[0].message)

    def test_save_bakes_svg_and_powerpoint(self, tmp_path: Path) -> None:
        def build(self: svg.Scene, doc: svg.Document) -> None:
            self.attach(doc.rect(10, 10, 20, 20, fill="gold"), breathe, amount=0.3, period=1)

        scene = scene_of(build)
        assert scene.save(tmp_path / "pulse.svg") == tmp_path / "pulse.svg"
        assert 'type="scale"' in (tmp_path / "pulse.svg").read_text(encoding="utf-8")
        scene.save(tmp_path / "pulse.pptx", ffmpeg="no-such-ffmpeg")
        assert (tmp_path / "pulse.pptx").stat().st_size > 0
        assert "animateTransform" in scene._repr_svg_()

    def test_frames_match_the_python_animation(self) -> None:
        def build(self: svg.Scene, doc: svg.Document) -> None:
            doc.rect(0, 0, 100, 60, fill="white")
            self.attach(doc.add(svg.preset.shape.get("star")(30, 30, 15, fill="gold")), wiggle, angle=25,
                        period=1)
            self.ring = doc.circle(70, 30, 8, fill="none", stroke="teal", stroke_width=3)
            self.ring.animate.fade_in(0.4)
            self.label = doc.text("0", x=5, y=55, font_size=10)

        def update(self: svg.Scene, t: float) -> None:
            self.ring.cx = 70 + 20 * math.sin(math.pi * t)
            self.ring.stroke = svg.Color(0, t, 1 - t)
            self.label.children[0] = str(int(t * 4))

        scene = scene_of(build, update, fps=24)
        baked = baked_quietly(scene)
        for seconds in (0.0, 0.2, 0.43, 0.5, 0.77, 1.0):
            assert mismatch(scene, baked, seconds) < PIXEL_TOLERANCE


def test_looping_scenes_repeat_forever():
    class Spin(svg.Scene):
        width, height, duration = 40, 40, 2.0
        loop = True

        def build(self, doc):
            self.dot = doc.circle(30, 20, 4)

        def update(self, seconds):
            self.dot.cx = 20 + 10 * (seconds / self.duration)

    looped = Spin().bake(fps=4).to_string()
    once = Spin().bake(fps=4, loop=False).to_string()
    assert 'repeatCount="indefinite"' in looped and 'repeatCount="indefinite"' not in once

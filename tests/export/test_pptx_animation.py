from __future__ import annotations

import io
import math
import zipfile

import pytest

import svgwriter as svg
from svgwriter.formats.export._office._anim_smil import Effect, smil_effect
from svgwriter.formats.export._office._pptx_anim import slide_animations
from svgwriter.formats.export._office._pptx_timing import timing_xml

pytest.importorskip("pptx")

KINDS = {
    "fade_in": lambda m: m.fade_in(1.5, begin=0.5, ease="ease-in-out"),
    "fade_out": lambda m: m.fade_out(1, begin=2),
    "appear": lambda m: m.show(0.25),
    "disappear": lambda m: m.hide(3),
    "motion": lambda m: m.move_by(40, 20, 2, begin=1),
    "rotate": lambda m: m.rotate(90, begin=1, repeat=2),
    "scale": lambda m: m.pulse(repeat=3),
    "color": lambda m: m.tween("fill", "red", "blue", 2, begin=1),
}


def _deck(build) -> bytes:
    doc = svg.Document(200, 100)
    build(doc.rect(10, 10, 40, 30, fill="red").animate)
    return svg.export.export(doc, "pptx")


def _read(data: bytes) -> list:
    back = svg.FORMATS.reader("pptx").read(data, slide=0)
    return [smil for smil in back.root.iter() if smil.tag in ("animate", "set", "animateTransform", "animateMotion")]


def _effects(data: bytes) -> list[Effect]:
    found = []
    for smil in _read(data):
        effect = smil_effect(smil, svg.Matrix())
        if effect is not None and effect.kind:
            found.append(effect)
    return found


class TestExport:
    def test_timing_written_into_slide(self) -> None:
        data = _deck(KINDS["fade_in"])
        slide = zipfile.ZipFile(io.BytesIO(data)).read("ppt/slides/slide1.xml").decode()
        assert "<p:timing" in slide and 'presetClass="entr"' in slide and 'delay="500"' in slide

    def test_first_effect_starts_by_itself(self) -> None:
        xml = timing_xml([(2, Effect("rotate", begin=1)), (2, Effect("appear"))], (10, 10))
        assert xml.index('nodeType="afterEffect"') < xml.index('nodeType="withEffect"')
        assert 'evt="onBegin"' in xml

    def test_entrance_shape_rests_visible(self) -> None:
        doc = svg.Document(20, 20)
        rect = doc.rect(0, 0, 5, 5)
        rect.animate.show(1).fade_in(begin=1)
        copy = slide_animations(doc).document.root.children[0]
        assert copy.get("visibility") is None and copy.get("opacity") is None
        assert rect.get("visibility") == "hidden"

    def test_unsupported_warned_once(self) -> None:
        doc = svg.Document(20, 20)
        path = doc.path("M0 0 L5 5")
        path.animate.morph(svg.path("M0 0 L5 0")).draw()
        with pytest.warns(UserWarning, match="dropped: animate d on <path>, animate stroke-dashoffset") as caught:
            svg.export.export(doc, "pptx")
        assert len([w for w in caught if "PowerPoint" in str(w.message)]) == 1

    def test_motion_in_slide_fractions(self) -> None:
        xml = timing_xml([(2, Effect("motion", points=((0, 0), (50, 25))))], (200, 100))
        assert 'path="M 0 0 L 0.25 0.25 E"' in xml

    def test_no_animation_no_timing(self) -> None:
        doc = svg.Document(20, 20)
        doc.rect(0, 0, 5, 5)
        slide = zipfile.ZipFile(io.BytesIO(svg.export.export(doc, "pptx"))).read("ppt/slides/slide1.xml")
        assert b"<p:timing" not in slide


class TestRoundTrip:
    @pytest.mark.parametrize("kind", KINDS)
    def test_kind_and_timing_survive(self, kind: str) -> None:
        doc = svg.Document(200, 100)
        KINDS[kind](doc.rect(10, 10, 40, 30, fill="red").animate)
        original = slide_animations(doc).effects["0"]
        found = _effects(_deck(KINDS[kind]))
        assert [e.kind for e in found] == [e.kind for e in original]
        for before, after in zip(original, found, strict=True):
            assert math.isclose(before.begin, after.begin, abs_tol=1e-3)
            assert math.isclose(before.dur, after.dur, abs_tol=1e-3) or kind in ("appear", "disappear")
            assert before.repeat == after.repeat and before.freeze == after.freeze
            assert math.isclose(before.accel, after.accel, abs_tol=1e-3)

    def test_values_survive(self) -> None:
        doc = svg.Document(200, 100)
        motion = doc.rect(10, 10, 40, 30, fill="red").animate
        motion.move_by(40, 20).rotate(45).tween("fill", "red", "#0000ff")
        exported = svg.export.export(doc, "pptx")
        found = {e.kind: e for e in _effects(exported)}
        assert found["motion"].points[-1] == pytest.approx((40, 20), abs=0.01)
        assert found["rotate"].angle == pytest.approx(45)
        assert found["color"].color == "#0000ff"

    def test_grow_and_slide_in(self) -> None:
        doc = svg.Document(200, 100)
        doc.rect(10, 10, 40, 30).animate.grow()
        doc.rect(60, 10, 40, 30).animate.slide_in("left", distance=50)
        effects = _effects(svg.export.export(doc, "pptx"))
        scale = next(e for e in effects if e.kind == "scale")
        assert scale.start == (0, 0) and scale.end == (1, 1)
        motion = next(e for e in effects if e.kind == "motion")
        assert motion.points[0] == pytest.approx((-50, 0), abs=0.01)

    def test_deck_without_timing_reads(self) -> None:
        doc = svg.Document(20, 20)
        doc.rect(0, 0, 5, 5)
        assert _read(svg.export.export(doc, "pptx")) == []

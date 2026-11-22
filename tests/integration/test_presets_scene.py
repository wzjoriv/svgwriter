"""Every preset kind in one scene with layout and theme roles; baking it and exporting it to PowerPoint."""

import warnings

import pytest

import svgwriter as svg

SLIDE_PX = 40


@pytest.fixture
def presets():
    @svg.preset.shape(role="accent")
    def integration_badge(cx: float, cy: float, r: float, **kwargs: object) -> svg.Circle:
        return svg.circle(cx, cy, r, **kwargs)

    @svg.preset.animation
    def integration_pop(motion: svg.Motion, *, dur: float = 1.0) -> svg.Motion:
        return motion.fade_in(dur)

    @svg.preset.behavior
    def integration_slide(element: svg.Element, seconds: float, *, dx: float = SLIDE_PX) -> None:
        element.t = element.home.t
        element.translate(dx * seconds, 0)

    svg.preset.size("integration-card", 320, 180)
    yield integration_badge
    for kind, name in (("shape", "integration_badge"), ("animation", "integration_pop"),
                       ("behavior", "integration_slide"), ("size", "integration-card")):
        svg.preset.KINDS[kind].unregister(name)


def scene(badge):
    class Card(svg.Scene):
        size = "integration-card"
        fps = 4
        duration = 1.0

        def build(self, doc: svg.Document) -> None:
            doc.theme = "dark"
            label = svg.text("Hi", font_size=12).as_role("text")
            self.card = svg.HStack(badge(0, 0, 10), label, gap=6, padding=8, background="surface")
            doc += self.card
            label.animate.integration_pop(dur=0.5)
            self.card.animate.integration_slide()

    return Card()


def test_presets_meet_in_one_scene(presets):
    card = scene(presets)
    doc = card.document
    assert (float(doc.root.get("width")), doc.theme.name) == (320, "dark")
    assert card.card[1].classes == ["role-accent"]
    assert card.render(0.5)[:4] == b"\x89PNG"


def test_baking_keeps_layout_roles_and_motion(presets):
    card = scene(presets)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        baked = card.bake()
    text = baked.to_string()
    assert baked.theme.name == "dark"
    assert all(f".role-{role}" in text for role in ("surface", "accent", "text"))
    assert "<animateTransform" in text and 'attributeName="opacity"' in text
    group = baked.at(1.0).root.find(svg.Group)
    assert group.t.apply(0, 0).x == pytest.approx(SLIDE_PX)


def test_powerpoint_of_the_baked_scene_keeps_the_effects(presets, tmp_path):
    pptx = pytest.importorskip("pptx")
    path = tmp_path / "card.pptx"
    scene(presets).save(path)
    slide = pptx.Presentation(str(path)).slides[0]
    xml = slide._element.xml
    assert "p:timing" in xml and "<p:animMotion" in xml and "<p:animEffect" in xml
    assert len(slide.shapes) >= 3

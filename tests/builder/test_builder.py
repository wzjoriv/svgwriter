from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter import builder
from tests.conftest import wellformed


class TestPresets:
    def test_presets(self) -> None:
        assert builder.outline(0, 0, 5, 5).get("fill") == "none"
        assert builder.outline(0, 0, 5, 5, stroke="red").style["stroke"] == "red"
        assert builder.dashed_line(0, 0, 5, 5).get("stroke-dasharray") == (4, 2)
        assert 'stroke-dasharray="4 2"' in str(builder.dashed_line(0, 0, 1, 1))
        assert builder.dashed_line(0, 0, 1, 1, stroke_dasharray="1").style["stroke-dasharray"] == "1"
        assert builder.dot(3, 4).get("r") == 2 and builder.dot(3, 4).classes == ["role-dot"]

    def test_presets_follow_the_document_theme(self) -> None:
        for name in ("light", "dark"):
            doc = svg.Document(20, 20, theme=name)
            doc += [builder.outline(1, 1, 18, 18), builder.dashed_line(0, 10, 20, 10), builder.dot(10, 10)]
            doc += builder.star(10, 10, 5, stroke="red")
            text = doc.to_string()
            theme = svg.Theme.get(name)
            for role in ("outline", "line", "dot", "shape"):
                assert str(theme.css([role])) in text

    def test_duplicates_of_the_aliases_are_gone(self) -> None:
        for name in ("rect", "circle", "document", "linear_gradient"):
            assert not hasattr(builder, name)


class TestRegistry:
    def test_builtin_shapes(self) -> None:
        assert {"star", "polygon", "gear", "arrow"} <= set(svg.SHAPES.names())
        star = svg.SHAPES.get("star")(50, 50, 40, fill="gold")
        assert len(star.points) == 10
        assert star.style["fill"] == "gold" and star.classes == ["role-shape"]
        assert builder.star.__name__ == "star"
        assert builder.star.__wrapped__ is not None  # type: ignore[attr-defined]
        assert len(svg.SHAPES.get("polygon")(0, 0, 5, sides=5).points) == 5
        assert len(svg.Polygon.regular(0, 0, 5).points) == 6
        assert len(builder.gear(0, 0, 10, teeth=8).points) == 32
        assert builder.arrow(0, 0, 10, 0).get("fill") == "none"
        assert builder.arrow(0, 0, 10, 0).classes == ["role-arrow-line"]

    def test_unthemed_plugin(self) -> None:
        @svg.shape_factory("test-plain", role=None)
        def plain(**kwargs: object) -> svg.Rect:
            return svg.Rect(0, 0, 1, 1, **kwargs)

        try:
            assert plain(fill="red").get("fill") == "red" and plain().classes == []
        finally:
            svg.SHAPES.remove("test-plain")

    def test_plugin_registration_and_validation(self) -> None:
        @svg.shape_factory("test-bad")
        def bad() -> svg.Element:
            return "nope"  # type: ignore[return-value]

        @svg.shape_factory("test-ok")
        def ok(size: float, **kwargs: object) -> svg.Rect:
            return svg.Rect.square(size, **kwargs)

        assert "test-ok" in svg.SHAPES and len(svg.SHAPES) >= 6
        assert ok(3).get("width") == 3
        with pytest.raises(TypeError):
            bad()
        with pytest.raises(ValueError):
            svg.shape_factory("test-ok")(ok)
        with pytest.raises(KeyError):
            svg.SHAPES.get("nothing")


class TestEffects:
    def test_drop_shadow_is_a_valid_graph(self) -> None:
        shadow = svg.drop_shadow(3, 3, 2, "navy", 0.4, id="shadow")
        results = {p.get("result") for p in shadow.primitives if p.has("result")}
        inputs = {p.get("in") for p in shadow.iter() if p.has("in")} | {p.get("in2") for p in shadow.iter() if p.has("in2")}
        standard = {svg.StandardInput.SOURCE_ALPHA, svg.StandardInput.SOURCE_GRAPHIC}
        assert inputs <= results | standard
        assert shadow.get("x") == "-20%"
        wellformed(svg.Svg(svg.Defs(shadow)).to_string())

    def test_glow_and_marker(self) -> None:
        assert len(builder.glow(4).primitives) == 2
        marker = builder.arrow_marker("red", 8, id="head")
        assert marker.get("orient") == "auto" and marker.view_box == svg.ViewBox(0, 0, 8, 8)

    def test_drawing_decorator(self) -> None:
        @svg.drawing(50, 40, id="pic")
        def picture(doc: svg.Document, color: str, *, radius: float = 5) -> None:
            doc.add(svg.Circle(25, 20, radius, fill=color))

        doc = picture("red", radius=8)
        assert isinstance(doc, svg.Document)
        assert doc.root.id == "pic"
        assert doc.root.find(svg.Circle).get("r") == 8  # type: ignore[union-attr]
        assert picture.__name__ == "picture"


class TestThemedMarker:
    def test_default_head_follows_the_theme(self) -> None:
        marker = svg.builder.arrow_marker()
        head = marker[0]
        assert head.classes == ["role-arrow-head"] and head.get("fill") == "black"
        doc = svg.Document(20, 20, theme="dark")
        doc.define(marker)
        assert ".role-arrow-head { fill:#e5e7eb" in doc.to_string()
        assert svg.builder.arrow_marker("red")[0].classes == []

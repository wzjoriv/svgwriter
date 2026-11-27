from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter import paths as builder


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
            theme = svg.themes.get(name)
            for role in ("outline", "line", "dot", "shape"):
                assert str(theme.css([role])) in text

    def test_duplicates_of_the_aliases_are_gone(self) -> None:
        for name in ("rect", "circle", "document", "linear_gradient"):
            assert not hasattr(builder, name)


class TestRegistry:
    def test_builtin_shapes(self) -> None:
        assert {"star", "polygon", "gear", "arrow"} <= set(svg.preset.shape.list())
        star = svg.preset.shape.get("star")(50, 50, 40, fill="gold")
        assert len(star.points) == 10
        assert star.style["fill"] == "gold" and star.classes == ["role-shape"]
        assert builder.star.__name__ == "star"
        assert builder.star.__wrapped__ is not None  # type: ignore[attr-defined]
        assert len(svg.preset.shape.get("polygon")(0, 0, 5, sides=5).points) == 5
        assert len(svg.Polygon.regular(0, 0, 5).points) == 6
        assert len(builder.gear(0, 0, 10, teeth=8).points) == 32
        assert builder.arrow(0, 0, 10, 0).get("fill") == "none"
        assert builder.arrow(0, 0, 10, 0).classes == ["role-arrow-line"]

    def test_unthemed_plugin(self) -> None:
        @svg.preset.shape(name="test-plain", role=None)
        def plain(**kwargs: object) -> svg.Rect:
            return svg.Rect(0, 0, 1, 1, **kwargs)

        try:
            assert plain(fill="red").get("fill") == "red" and plain().classes == []
        finally:
            svg.preset.shape.unregister("test-plain")

    def test_plugin_registration_and_validation(self) -> None:
        @svg.preset.shape(name="test-bad")
        def bad() -> svg.Element:
            return "nope"  # type: ignore[return-value]

        @svg.preset.shape(name="test-ok")
        def ok(size: float, **kwargs: object) -> svg.Rect:
            return svg.Rect.square(size, **kwargs)

        try:
            assert "test-ok" in svg.preset.shape.list() and len(svg.preset.shape.list()) >= 6
            assert ok(3).get("width") == 3
            with pytest.raises(TypeError):
                bad()
            with pytest.raises(ValueError, match="already registered by .*ok; pass replace=True"):
                svg.preset.shape(name="test-ok")(ok)
            with pytest.raises(KeyError, match="unknown shape 'nothing'"):
                svg.preset.shape.get("nothing")
        finally:
            svg.preset.shape.unregister("test-ok")
            svg.preset.shape.unregister("test-bad")

    def test_replace_builtin_and_restore(self) -> None:
        original = svg.preset.shape.get("star")
        with pytest.raises(ValueError, match=r"star \(built in\)"):
            svg.preset.shape(name="star")(svg.Rect.square)

        @svg.preset.shape(name="star", replace=True)
        def square_star(cx: float, cy: float, r: float, **kwargs: object) -> svg.Rect:
            return svg.Rect(cx - r, cy - r, 2 * r, 2 * r, **kwargs)

        try:
            assert svg.preset.shape.get("star")(0, 0, 1).tag == "rect"
        finally:
            svg.preset.shape.unregister("star")
        assert svg.preset.shape.get("star") is original
        with pytest.raises(KeyError, match="built in"):
            svg.preset.shape.unregister("star")

    def test_unknown_kind(self) -> None:
        with pytest.raises(AttributeError, match="nope"):
            svg.preset.nope.list()


class TestDrawing:
    def test_drawing_decorator(self) -> None:
        @svg.drawing(50, 40, id="pic")
        def picture(doc: svg.Document, color: str, *, radius: float = 5) -> None:
            doc.add(svg.Circle(25, 20, radius, fill=color))

        doc = picture("red", radius=8)
        assert isinstance(doc, svg.Document)
        assert doc.root.id == "pic"
        assert doc.root.find(svg.Circle).get("r") == 8  # type: ignore[union-attr]
        assert picture.__name__ == "picture"



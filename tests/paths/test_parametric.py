from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.library.paths import Arc, Star, parametric


class TestStar:
    def test_rounded_matches_inkscape(self) -> None:
        path = Star.create(150, 70, 20, 10, 5, rounded=0.3)
        first = path.d[1]
        assert (first.x1, first.y1) == pytest.approx((153.98439, 50), abs=1e-4)

    def test_polygon(self) -> None:
        hexagon = svg.paths.regular_polygon(0, 0, 10, 6, parametric=True)
        assert Star(hexagon).flatsided and hexagon.bbox.height == pytest.approx(20)

    def test_builder_star_matches_plain_star(self) -> None:
        drawn = svg.paths.star(50, 50, 40, parametric=True, fill="gold")
        plain = svg.paths.star(50, 50, 40)
        assert drawn.bbox.width == pytest.approx(plain.bbox.width)
        with pytest.raises(ValueError, match="corner_radius"):
            svg.paths.star(0, 0, 4, parametric=True, corner_radius=1)

    def test_edits_survive_a_plain_document(self) -> None:
        doc = svg.Document(100, 100)
        star = parametric(doc.add(svg.paths.star(50, 50, 40, parametric=True, id="s")))
        star.sides, star.skew = 8, 5
        back = parametric(svg.Document.from_string(doc.to_string())["s"])
        assert isinstance(back, Star) and back.sides == 8 and back.skew == pytest.approx(5)

    def test_exports_as_a_path(self) -> None:
        doc = svg.Document(100, 100)
        doc.add(svg.paths.star(50, 50, 40, parametric=True))
        assert doc.export("pdf").startswith(b"%PDF")

    def test_not_a_star(self) -> None:
        with pytest.raises(ValueError, match="not a parametric star"):
            Star(svg.Path("M0 0"))


class TestArc:
    def test_kinds(self) -> None:
        pie = Arc.create(0, 0, 10, 10, start=0, end=90)
        assert Arc(pie).kind == "slice" and str(pie.d).count("Z") == 1
        Arc(pie).kind = "arc"
        assert str(pie.d).count("Z") == 0
        with pytest.raises(ValueError):
            Arc(pie).kind = "wedge"

    def test_whole_ellipse(self) -> None:
        assert Arc.create(5, 5, 4, 2).bbox.width == pytest.approx(8)


def test_parametric_ignores_other_elements() -> None:
    assert parametric(svg.rect(0, 0, 1, 1)) is None
    assert isinstance(parametric(Arc.create(0, 0, 1, 1)), Arc)

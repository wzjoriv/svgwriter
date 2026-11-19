from __future__ import annotations

import math

import pytest

import svgwriter as svg
from svgwriter.color import Color
from svgwriter.pathdata import PathData
from svgwriter.pathdata._affine import transform_arc
from svgwriter.pathdata.commands import ArcTo
from svgwriter.transform import Matrix, Point, Rotate, Transform


class TestContainerOperators:
    def test_iadd_single_and_list(self) -> None:
        group = svg.Group()
        group += svg.Circle()
        group += [svg.Rect(), svg.Line()]
        group += (e for e in [svg.Ellipse()])
        assert [c.tag for c in group] == ["circle", "rect", "line", "ellipse"]

    def test_iadd_rejects_non_elements(self) -> None:
        group = svg.Group()
        with pytest.raises(TypeError, match="iterable of elements"):
            group += object()  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="expected elements"):
            group += [svg.Rect(), 3]  # type: ignore[list-item]

    def test_document_iadd_respects_insertion_point(self) -> None:
        doc = svg.Document(10, 10)
        with doc.group() as g:
            doc += svg.Rect()
            doc += [svg.Circle(), svg.Line()]
        assert len(g) == 3 and len(doc.root) == 1

    def test_plus_makes_a_new_group(self) -> None:
        a, b, c = svg.Rect(), svg.Circle(), svg.Line()
        group = a + b
        assert isinstance(group, svg.Group) and list(group) == [a, b]
        assert list(svg.Group(id="g") + [c]) [1] is c
        assert list([svg.Rect(), svg.Rect()] + svg.Circle())[2].tag == "circle"

    def test_plus_rejects_other_types(self) -> None:
        with pytest.raises(TypeError):
            _ = svg.Rect() + object()  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = svg.Rect() + (1, 2, 3)  # type: ignore[operator]

    def test_mod_is_gone(self) -> None:
        with pytest.raises(TypeError):
            _ = svg.Document() % svg.Symbol()  # type: ignore[operator]


class TestAutoDefs:
    def test_reference_defines_on_add(self) -> None:
        doc = svg.Document(10, 10)
        grad = svg.LinearGradient.horizontal("red", "blue")
        rect = doc.rect(0, 0, 10, 10, fill=grad)
        assert grad.parent is doc.defs and str(rect.get("fill")) == f"url(#{grad.id})"
        doc.circle(5, 5, 1, fill=grad)
        assert len(doc.defs) == 1

    def test_detached_subtree_defines_when_added(self) -> None:
        doc = svg.Document(10, 10)
        clip = svg.ClipPath(svg.Circle(5, 5, 5))
        group = svg.Group(svg.Rect(0, 0, 10, 10, clip_path=clip))
        assert clip.parent is None
        doc += group
        assert clip.parent is doc.defs

    def test_setting_reference_inside_document(self) -> None:
        doc = svg.Document(10, 10)
        rect = doc.rect(0, 0, 1, 1)
        rect.fill = svg.Pattern(id="p")
        assert doc.defs[0].id == "p"

    def test_href_is_plain_iri(self) -> None:
        doc = svg.Document(10, 10)
        use = doc.use(svg.Symbol(id="star"))
        assert str(use.get("xlink:href")) == "#star" and doc.defs[0].id == "star"

    def test_placed_target_is_not_moved(self) -> None:
        doc = svg.Document(10, 10)
        r = doc.rect(0, 0, 1, 1, id="r")
        doc.use(r)
        assert r.parent is doc.root

    def test_explicit_define(self) -> None:
        doc = svg.Document(10, 10)
        doc.defs += svg.Marker(id="m")
        doc.define(svg.Symbol())
        assert len(doc.defs) == 2

    def test_reference_round_trips(self) -> None:
        doc = svg.Document(10, 10)
        doc.rect(0, 0, 1, 1, fill=svg.LinearGradient(id="g"))
        assert 'fill="url(#g)"' in doc.to_string() and "<linearGradient id=\"g\"" in doc.to_string()


class TestPathOperators:
    def test_path_concatenation(self) -> None:
        a = svg.Path("M0 0 H10", stroke="red")
        b = svg.Path("M0 5 H10")
        joined = a + b
        assert isinstance(joined, svg.Path) and str(joined.d) == "M0 0 H10 M0 5 H10"
        assert joined.get("stroke") == "red" and str(a.d) == "M0 0 H10"
        assert str((a + "M1 1 L2 2").d).endswith("L2 2")
        assert str((a + PathData("M3 3")).d).endswith("M3 3")
        assert isinstance(a + svg.Circle(), svg.Group)

    def test_path_in_place_concatenation(self) -> None:
        a = svg.Path("M0 0 H1")
        same = a
        a += svg.Path("M5 5 H6")
        a += "M7 7 H8"
        assert a is same and len(a.d) == 6

    def test_path_data_add_and_sum(self) -> None:
        pieces = [PathData("M0 0 H1"), PathData("M2 2 H3")]
        assert str(sum(pieces, PathData())) == "M0 0 H1 M2 2 H3"
        assert str(sum(pieces)) == "M0 0 H1 M2 2 H3"
        assert str("M9 9" + PathData("M1 1")) == "M9 9 M1 1"
        assert len((PathData("M0 0 H1") + "M2 2 H3").subpaths()) == 2

    def test_arc_transform_is_exact(self) -> None:
        arc = ArcTo(10, 5, 0, False, True, 20, 0)
        rotated = transform_arc(arc, Matrix.rotate(90))
        assert math.isclose(rotated.rx, 10) and math.isclose(rotated.ry, 5)
        assert math.isclose(abs(rotated.rotation), 90)
        flipped = transform_arc(arc, Matrix.scale(1, -1))
        assert flipped.sweep is False
        scaled = transform_arc(ArcTo(1, 1, 0, False, True, 2, 0), Matrix.scale(3, 2))
        assert math.isclose(scaled.rx, 3) and math.isclose(scaled.ry, 2)

    def test_arc_bbox_survives_rotation(self) -> None:
        d = PathData("M0 0 A10 5 0 0 1 20 0")
        box = (Transform.rotate(90) @ d).bbox
        assert box is not None and math.isclose(box.height, 20, abs_tol=1e-6) and math.isclose(box.width, 5, abs_tol=0.1)

    def test_transform_handles_every_command(self) -> None:
        d = PathData("M0 0 h1 v1 c1 1 2 2 3 3 s1 1 2 2 q1 1 2 2 t1 1 a1 1 0 0 1 1 1 z")
        moved = d.transformed(Transform.translate(1, 1))
        assert len(moved) == len(d) and str(moved).startswith("M1 1 L2 1")


class TestShapeToPath:
    @pytest.mark.parametrize(
        ("shape", "expected"),
        [
            (svg.Rect(1, 2, 3, 4), "M1 2 H4 V6 H1 V2 Z"),
            (svg.Line(0, 0, 3, 4), "M0 0 L3 4"),
            (svg.Polyline([(0, 0), (1, 1)]), "M0 0 L1 1"),
            (svg.Polygon([(0, 0), (1, 1), (1, 0)]), "M0 0 L1 1 L1 0 Z"),
            (svg.Circle(5, 5, 2), "M3 5 A2 2 0 0 1 7 5 A2 2 0 0 1 3 5 Z"),
            (svg.Ellipse(0, 0, 2, 1), "M-2 0 A2 1 0 0 1 2 0 A2 1 0 0 1 -2 0 Z"),
            (svg.Path("M0 0 h5"), "M0 0 h5"),
        ],
    )
    def test_outline(self, shape: svg.Shape, expected: str) -> None:
        assert str(shape.to_path().d) == expected

    def test_rounded_rect_and_radius_rules(self) -> None:
        rect = svg.Rect(0, 0, 10, 4, rx=3)
        assert rect.corner_radii() == (3, 2)
        assert str(rect.to_path().d).count("A") == 4
        assert svg.Rect(0, 0, 10, 10, ry=2).corner_radii() == (2, 2)

    def test_to_path_copies_presentation_not_geometry(self) -> None:
        circle = svg.Circle(5, 5, 2, id="c", fill="red", class_="dot", transform="translate(10)")
        path = circle.to_path(stroke="blue")
        assert path.attributes.keys() >= {"d", "fill", "class", "stroke"}
        assert not {"id", "cx", "r", "transform"} & path.attributes.keys()
        assert str(path.d).startswith("M13 5")

    def test_empty_polygon(self) -> None:
        assert len(svg.Polygon().to_path().d) == 0

    def test_base_operand_has_no_outline(self) -> None:
        with pytest.raises(TypeError):
            svg.PathOperand().local_outline()


class TestTransformOperators:
    def test_class_level_builders(self) -> None:
        assert str(Transform.rotate(30) @ Transform.scale(2)) == "rotate(30) scale(2)"
        assert str(Transform.translate(1, 2).skew_x(5)) == "translate(1 2) skewX(5)"
        assert str(Transform.matrix(1, 0, 0, 1, 0, 0)) == "matrix(1 0 0 1 0 0)"
        assert Transform.skew_y.__name__ == "skew_y"

    def test_instance_builders_still_chain(self) -> None:
        t = Transform()
        assert t.translate(5) is t and len(t) == 1

    def test_matmul_with_ops_matrices_and_points(self) -> None:
        t = Transform.translate(10)
        assert str(t @ Rotate(90)) == "translate(10) rotate(90)"
        assert str(Rotate(90) @ t) == "rotate(90) translate(10)"
        assert str(t @ Matrix.scale(2)) == "translate(10) matrix(2 0 0 2 0 0)"
        assert str(Matrix.scale(2) @ t) == "matrix(2 0 0 2 0 0) translate(10)"
        assert t @ (1, 1) == Point(11, 1)
        assert Matrix.scale(3) @ Point(1, 2) == Point(3, 6)

    def test_in_place_matmul(self) -> None:
        t = Transform.translate(1)
        same = t
        t @= Transform.scale(2)
        t @= Rotate(5)
        assert t is same and len(t) == 3

    def test_inverse(self) -> None:
        t = Transform.translate(3, 4).scale(2)
        assert (t @ t.inverse()).to_matrix().isclose(Matrix())

    def test_bad_operands(self) -> None:
        with pytest.raises(TypeError):
            _ = Transform() @ 3  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = Matrix() @ "x"  # type: ignore[operator]
        t = Transform()
        with pytest.raises(TypeError):
            t @= 3  # type: ignore[operator]

    def test_parse_error_message(self) -> None:
        with pytest.raises(ValueError, match=r"rotate\(\) takes 1 or 3 arguments, got 2"):
            Transform.parse("rotate(1 2)")


class TestColorOperators:
    def test_add_mixes(self) -> None:
        red, blue = Color.parse("red"), Color.parse("blue")
        assert (red + blue).hex == "#800080"
        assert (red + "blue").hex == "#800080"
        assert ("blue" + red).hex == "#800080"

    def test_multiply_and_divide(self) -> None:
        white = Color.parse("white")
        assert (white * 0.5).hex == "#808080"
        assert (0.5 * white).hex == "#808080"
        assert (white / 2).hex == "#808080"
        assert (Color.from_uint8(200, 100, 50) * 2).hex == "#ffc864"
        assert (Color.parse("red") * Color(1, 0.5, 0)).hex == "#ff0000"

    def test_in_place_forms_rebind(self) -> None:
        c = Color.parse("white")
        c *= 0.5
        c += Color(0, 0, 0)
        assert c.hex == "#404040"

    def test_bad_operands(self) -> None:
        with pytest.raises(TypeError):
            _ = Color(0, 0, 0) + 3  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = Color(0, 0, 0) * "x"  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = Color(0, 0, 0) / "x"  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = [1] + Color(0, 0, 0)  # type: ignore[operator]

    def test_channel_error_names_the_channel(self) -> None:
        with pytest.raises(ValueError, match="g=300"):
            Color(0, 300, 0)  # noqa: B018

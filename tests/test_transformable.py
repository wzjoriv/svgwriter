from __future__ import annotations

import math

import pytest

import svgwriter as svg
from svgwriter import Matrix, Transform


def close(p, q, tol=1e-9) -> bool:
    return all(math.isclose(a, b, abs_tol=tol) for a, b in zip(p, q, strict=False))


class TestT:
    def test_geometry_stays_local(self) -> None:
        c = svg.Circle(50, 50, 10).translate(5, 0)
        assert c.cx == 50 and str(c.t) == "translate(5)"
        assert 'cx="50"' in str(c) and 'transform="translate(5)"' in str(c)

    def test_translates_merge_in_parent_frame(self) -> None:
        c = svg.Circle(0, 0, 1).translate(1, 2).translate(3, 4)
        assert str(c.t) == "translate(4 6)"

    def test_assign_and_clear(self) -> None:
        r = svg.Rect(0, 0, 10, 10, t="scale(2)")
        assert str(r.t) == "scale(2)" and r.transform == r.t
        r.t = None
        assert not r.has("transform")
        r.t = Matrix.translate(1)
        assert r.t.isclose(Matrix.translate(1)) and str(r.t) == "translate(1)"

    def test_t_is_an_immutable_matrix(self) -> None:
        r = svg.Rect(0, 0, 1, 1)
        assert isinstance(r.t, Matrix) and r.t.is_identity
        with pytest.raises(AttributeError):
            r.t.e = 5  # type: ignore[misc]

    def test_composes_into_one_matrix(self) -> None:
        r = svg.Rect(0, 0, 10, 10).translate(5).rotate(90).scale(2).translate(-5)
        assert str(r.t).count("(") <= 2 and r.t.isclose(
            Matrix.translate(-5) @ Matrix.translate(10, 5) @ Matrix.scale(2) @ Matrix.translate(-10, -5)
            @ Matrix.rotate(90, 10, 5) @ Matrix.translate(5)
        )

    def test_parsed_transform_is_kept_until_changed(self) -> None:
        r = svg.parse('<rect transform="translate(1) translate(2)"/>')
        assert str(r.get("transform")) == "translate(1) translate(2)" and r.t.isclose("translate(3)")
        r.rotate(0)
        assert str(r.get("transform")) == "translate(3)"

    def test_reset(self) -> None:
        assert not svg.Rect(0, 0, 1, 1).rotate(5).reset().has("transform")


class TestAnchor:
    def test_default_is_bbox_centre_and_follows_geometry(self) -> None:
        r = svg.Rect(0, 0, 10, 20)
        assert r.anchor == (5, 10)
        r.width = 30
        assert r.anchor == (15, 10)

    def test_pinned(self) -> None:
        r = svg.Rect(0, 0, 10, 10, anchor=(0, 0))
        assert r.anchor == (0, 0)
        r.anchor = None
        assert r.anchor == (5, 5)

    def test_rotate_about_anchor(self) -> None:
        r = svg.Rect(0, 0, 10, 10).rotate(90)
        assert str(r.t) == "rotate(90 5 5)"
        assert close(r.position, (5, 5))

    def test_scale_about_anchor_keeps_position(self) -> None:
        c = svg.Circle(50, 50, 10).scale(2)
        assert close(c.position, (50, 50))
        assert close(c.bounds(), (30, 30, 40, 40))

    def test_explicit_pivot(self) -> None:
        c = svg.Circle(10, 0, 1).rotate(90, about=(0, 0))
        assert close(c.position, (0, 10))

    def test_group_anchor_is_children_centre(self) -> None:
        g = svg.Group(svg.Rect(0, 0, 10, 10), svg.Rect(20, 0, 10, 10).translate(0, 10))
        assert g.anchor == (15, 10)


class TestFrames:
    def test_parent_translate_ignores_rotation(self) -> None:
        r = svg.Rect(0, 0, 2, 2).rotate(90).translate(10, 0)
        assert close(r.position, (11, 1))

    def test_local_translate_follows_rotation(self) -> None:
        r = svg.Rect(0, 0, 2, 2).rotate(90).translate(10, 0, local=True)
        assert close(r.position, (1, 11))

    def test_local_vs_parent_scale_differ_after_rotation(self) -> None:
        a = svg.Rect(0, 0, 2, 2).rotate(90).scale(3, 1)
        b = svg.Rect(0, 0, 2, 2).rotate(90).scale(3, 1, local=True)
        assert close(a.bounds(), (-2, 0, 6, 2)) and close(b.bounds(), (0, -2, 2, 6))

    def test_skew(self) -> None:
        r = svg.Rect(0, 0, 2, 2).skew(45)
        box = r.bounds()
        assert math.isclose(box.width, 4) and close(r.position, (1, 1))

    def test_apply(self) -> None:
        r = svg.Rect(0, 0, 1, 1).apply("translate(1 2)")
        assert str(r.t) == "translate(1 2)"


class TestPosition:
    def test_set_position(self) -> None:
        c = svg.Circle(0, 0, 5)
        c.position = (10, 20)
        assert close(c.position, (10, 20)) and str(c.t) == "translate(10 20)"

    def test_place_at_chains(self) -> None:
        assert close(svg.Rect(0, 0, 4, 4).rotate(30).place_at(0, 0).position, (0, 0))

    def test_no_bbox_bounds_is_none(self) -> None:
        assert svg.Image("a.png").bounds() is None and svg.Image("a.png").anchor == (0, 0)

    def test_image_and_use_bboxes(self) -> None:
        assert svg.Image("a.png", 1, 2, 3, 4).bounds() == (1, 2, 3, 4)
        doc = svg.Document(10, 10)
        r = doc.define(svg.Rect(0, 0, 2, 2))
        u = doc.add(svg.Use(r, x=5))
        assert u.bounds() == (5, 0, 2, 2)


class TestOperators:
    def test_matrix_at_element_is_parent_frame_copy(self) -> None:
        r = svg.Rect(0, 0, 2, 2, fill="red").rotate(90)
        moved = Transform.translate(10) @ r
        assert isinstance(moved, svg.Rect) and moved is not r
        assert close(moved.position, (11, 1)) and close(r.position, (1, 1))

    def test_element_at_matrix_is_local_frame_copy(self) -> None:
        r = svg.Rect(0, 0, 2, 2).rotate(90)
        assert close((r @ Matrix.translate(10)).position, (1, 11))
        assert close((r @ "translate(10)").position, (1, 11))

    def test_times_number_scales_copy(self) -> None:
        c = svg.Circle(5, 5, 1)
        assert close((c * 3).bounds(), (2, 2, 6, 6)) and close((2 * c).bounds(), (3, 3, 4, 4))
        assert close((c * (2, 1)).bounds(), (3, 4, 4, 2))

    def test_times_transform_points_to_at(self) -> None:
        with pytest.raises(TypeError, match="@"):
            _ = svg.Circle() * Transform.scale(2)

    def test_junk_rejected(self) -> None:
        with pytest.raises(TypeError):
            _ = svg.Circle() @ object()  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = svg.Circle() + (1, "x")  # type: ignore[operator]
        with pytest.raises(ZeroDivisionError):
            _ = svg.Circle() / 0
        with pytest.raises(TypeError):
            _ = svg.Circle() * "x"  # type: ignore[operator]

    def test_to_path_bakes(self) -> None:
        p = svg.Rect(0, 0, 1, 1, fill="red").translate(2).to_path()
        assert str(p.d) == "M2 0 L3 0 L3 1 L2 1 L2 0 Z" and not p.has("transform")


class TestPaintServers:
    def test_gradient_t_maps_to_gradient_transform(self) -> None:
        g = svg.LinearGradient().rotate(90)
        assert str(g.get("gradientTransform")) == "rotate(90 0.5 0.5)" and not g.has("transform")

    def test_user_space_anchor(self) -> None:
        g = svg.RadialGradient(cx=10, cy=20, r=5, gradient_units="userSpaceOnUse")
        assert g.anchor == (10, 20)
        lin = svg.LinearGradient(x1=0, y1=0, x2=10, y2=0, gradient_units="userSpaceOnUse")
        assert lin.anchor == (5, 0)

    def test_pattern(self) -> None:
        p = svg.Pattern(x=0, y=0, width=10, height=10).scale(2)
        assert str(p.get("patternTransform")) == "matrix(2 0 0 2 -5 -5)" and p.anchor == (5, 5)

    def test_clip_path(self) -> None:
        cp = svg.ClipPath(svg.Circle(5, 5, 5)).translate(1)
        assert cp.anchor == (5, 5) and str(cp.t) == "translate(1)"


def test_path_move_to_draws_and_place_at_places() -> None:
    p = svg.Path().move_to(0, 0).line_to(10, 0).place_at(100, 100)
    assert str(p.d) == "M0 0 L10 0" and close(p.position, (100, 100))


def test_path_anchor_follows_edits_unless_pinned() -> None:
    p = svg.Path().move_to(0, 0).line_to(10, 0)
    assert p.anchor == (5, 0)
    p.line_to(10, 20)
    assert p.anchor == (5, 10)
    p.anchor = (0, 0)
    p.line_to(100, 100)
    assert p.anchor == (0, 0)


class TestConciseOutput:
    @pytest.mark.parametrize(
        ("build", "text"),
        [
            (lambda: svg.Rect(0, 0, 10, 10).rotate(90), "rotate(90 5 5)"),
            (lambda: svg.Rect(0, 0, 10, 10).translate(3, 4), "translate(3 4)"),
            (lambda: svg.Rect(0, 0, 10, 10).scale(2, about=(0, 0)), "scale(2)"),
            (lambda: svg.Rect(0, 0, 10, 10).skew(30, about=(0, 0)), "skewX(30)"),
            (lambda: svg.Rect(0, 0, 10, 10).scale(1, -1, about=(0, 0)), "scale(1 -1)"),
            (lambda: svg.Rect(0, 0, 10, 10).rotate(45).rotate(-45), None),
        ],
    )
    def test_shortest_text(self, build, text) -> None:
        el = build()
        assert el.get("transform") is None if text is None else str(el.get("transform")) == text


TRANSFORMABLE_TAGS = {
    "rect", "circle", "ellipse", "line", "polyline", "polygon", "path", "text", "g", "use", "image", "a",
    "switch", "defs", "clipPath", "linearGradient", "radialGradient", "pattern",
}


@pytest.mark.parametrize("tag", sorted(TRANSFORMABLE_TAGS))
def test_every_transformable_element_has_the_methods(tag: str) -> None:
    cls = svg.Element.lookup(tag)
    assert cls is not None and issubclass(cls, svg.elements.Transformable)
    el = cls()
    el.translate(1, 2).rotate(10).scale(2).skew(5)
    attribute = {"linearGradient": "gradientTransform", "radialGradient": "gradientTransform",
                 "pattern": "patternTransform"}.get(tag, "transform")
    assert el.has(attribute) and not el.t.is_identity


def test_no_other_element_pretends_to_transform() -> None:
    extra = {tag for tag, cls in svg.Element.registered().items() if issubclass(cls, svg.elements.Transformable)}
    assert extra == TRANSFORMABLE_TAGS


class TestArithmetic:
    def test_plus_minus_translate_copies(self) -> None:
        c = svg.Circle(0, 0, 1)
        assert close((c + (3, 4)).position, (3, 4)) and close((c - (3, 4)).position, (-3, -4))
        assert close((c + 2).position, (2, 2)) and close(((1, 1) + c).position, (1, 1))
        assert c.t.is_identity

    def test_in_place(self) -> None:
        c = svg.Circle(0, 0, 1)
        same = c
        c += (5, 0)
        c -= (1, 0)
        c *= 2
        c /= 2
        c @= 90
        assert c is same and close(c.position, (4, 0)) and c.bounds() == pytest.approx((3, -1, 2, 2))

    def test_at_number_rotates_about_anchor(self) -> None:
        r = svg.Rect(0, 0, 4, 2) @ 90
        assert str(r.t) == "rotate(90 2 1)" and r.bounds() == pytest.approx((1, -1, 2, 4))

    def test_divide(self) -> None:
        assert (svg.Circle(5, 5, 4) / 2).bounds() == pytest.approx((3, 3, 4, 4))
        assert (svg.Circle(5, 5, 4) / (2, 1)).bounds() == pytest.approx((3, 1, 4, 8))

    def test_element_operands_keep_their_meaning(self) -> None:
        a, b = svg.Rect(0, 0, 10, 10), svg.Rect(5, 0, 10, 10)
        assert isinstance(a + b, svg.Group)
        assert (a - b).exact_bbox() == (0, 0, 5, 10)

    def test_path_in_place_offsets(self) -> None:
        p = svg.Path("M0 0 L10 0")
        p -= (1, 1)
        p += (0, 3)
        assert str(p.d) == "M0 0 L10 0" and close(p.position, (4, 2))
        p += svg.Path("M0 5 H1")
        assert str(p.d) == "M0 0 L10 0 M0 5 H1"

    def test_group_plus_equals(self) -> None:
        g = svg.Group()
        g += svg.Rect(0, 0, 1, 1)
        g += (10, 0)
        assert len(g) == 1 and close(g.position, (10.5, 0.5))

    def test_numpy_operands(self) -> None:
        np = pytest.importorskip("numpy")
        c = svg.Circle(0, 0, 1) + np.array([2.0, 3.0])
        assert close(c.position, (2, 3))
        assert close((svg.Circle(0, 0, 1) + np.float32(1.5)).position, (1.5, 1.5))
        assert (svg.Circle(0, 0, 1) * np.int64(2)).bounds() == pytest.approx((-2, -2, 4, 4))


class TestFlip:
    def test_flip_about_anchor(self) -> None:
        tri = svg.Polygon([(0, 0), (10, 0), (0, 5)]).flip_x()
        assert tri.bounds() == pytest.approx((0, 0, 10, 5)) and str(tri.t) == "matrix(-1 0 0 1 10 0)"
        assert close(tri.t.apply(0, 0), (10, 0))
        assert close(svg.Rect(0, 0, 4, 4).flip_y().t.apply(0, 0), (0, 4))

    def test_flip_twice_is_identity_and_about(self) -> None:
        assert svg.Rect(0, 0, 4, 4).flip_x().flip_x().t.is_identity
        assert close(svg.Circle(5, 0, 1).flip_x(about=(0, 0)).position, (-5, 0))

    def test_matrix_flips(self) -> None:
        assert Matrix.flip_x(3).apply(1, 7) == (5, 7) and Matrix.flip_y(1).apply(4, 0) == (4, 2)


def test_text_rotate_is_the_transform_and_rotate_underscore_is_per_glyph() -> None:
    t = svg.Text("Hi", x=0, y=10, rotate=[5, 10])
    t.rotate(30, about=(0, 0))
    assert str(t.get("transform")) == "rotate(30)" and t.rotate_ == (5, 10)


class TestNumpy:
    def test_polyline_points_are_a_read_only_array(self) -> None:
        np = pytest.importorskip("numpy")
        xs = np.linspace(0, 10, 5)
        line = svg.Polyline(np.column_stack((xs, xs ** 2)))
        assert line.points.shape == (5, 2) and not line.points.flags.writeable
        assert str(line).startswith('<polyline points="0,0 2.5,6.25')
        assert line.bbox == (0, 0, 10, 100)

    def test_points_from_text_and_validation(self) -> None:
        p = svg.Polygon("0,0 4,0 4,3")
        assert p.points.tolist() == [[0, 0], [4, 0], [4, 3]] and p.area == 6
        with pytest.raises(ValueError, match=r"shape \(N, 2\)"):
            svg.Polygon([[1, 2, 3]])
        assert svg.Polygon().points.shape == (0, 2) and svg.Polygon() .bbox == (0, 0, 0, 0)

    def test_parsed_points_become_arrays_and_compare(self) -> None:
        p = svg.parse('<polygon points="1,2 3,4"/>')
        assert p.points.tolist() == [[1, 2], [3, 4]]
        assert svg.Polygon([(1, 2), (3, 4)]).attributes == svg.Polygon([(1, 2), (3, 4)]).attributes

    def test_matrix_maps_arrays_batch_and_broadcast(self) -> None:
        np = pytest.importorskip("numpy")
        m = Matrix.rotate(90)
        batch = np.zeros((3, 4, 2)) + [1, 0]
        out = m @ batch
        assert out.shape == (3, 4, 2) and np.allclose(out[..., 0], 0) and np.allclose(out[..., 1], 1)
        assert np.allclose(m @ np.array([1.0, 0.0]), [0, 1])
        with pytest.raises(ValueError, match="last axis"):
            m @ np.zeros((2, 3))

    def test_matrix_array_round_trip(self) -> None:
        np = pytest.importorskip("numpy")
        m = Matrix(1, 2, 3, 4, 5, 6)
        assert np.asarray(m).shape == (3, 3) and Matrix.from_array(np.asarray(m)) == m
        assert Matrix.from_array(np.asarray(m) @ np.asarray(Matrix.translate(1))).isclose(m @ Matrix.translate(1))
        with pytest.raises(ValueError):
            Matrix.from_array(np.eye(4))

    def test_color_array(self) -> None:
        np = pytest.importorskip("numpy")
        assert np.allclose(np.asarray(svg.Color(1, 0.5, 0)), [1, 0.5, 0, 1])
        assert svg.Rect(fill=np.array([0, 0, 1.0])).get("fill").hex == "#0000ff"

from __future__ import annotations

import math

import pytest

from svgwriter.transform import (
    IDENTITY,
    Matrix,
    MatrixOp,
    Point,
    Rotate,
    Scale,
    SkewX,
    SkewY,
    Transform,
    Translate,
    as_transform,
    parse_transform,
)


def test_builder_and_str() -> None:
    t = Transform().translate(10, 20).rotate(45).scale(2).skew_x(10).skew_y(5)
    assert str(t) == "translate(10 20) rotate(45) scale(2) skewX(10) skewY(5)"
    assert len(t) == 5
    assert isinstance(t[1], Rotate)
    assert len(t[1:3]) == 2


def test_parse_all_functions() -> None:
    t = parse_transform("matrix(1,0,0,1,5,6) translate(3) scale(2, 3) rotate(30 1 1),skewX(1) skewY(2)")
    assert [type(op) for op in t] == [MatrixOp, Translate, Scale, Rotate, SkewX, SkewY]
    assert t == Transform.parse(str(t))


@pytest.mark.parametrize("bad", ["translate(1, 2, 3)", "rotate(1, 2)", "spin(4)", "scale(1) junk"])
def test_parse_rejects(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_transform(bad)


def test_matrix_composition_order() -> None:
    m = Matrix.translate(10, 0) @ Matrix.scale(2)
    assert m.apply(1, 1) == Point(12.0, 2.0)
    t = Transform().translate(10, 0).scale(2)
    assert t.apply(1, 1) == Point(12.0, 2.0)


def test_rotate_about_center() -> None:
    m = Matrix.rotate(90, 5, 5)
    x, y = m.apply(10, 5)
    assert (x, y) == pytest.approx((5, 10))


def test_inverse() -> None:
    m = Matrix.translate(3, 4) @ Matrix.rotate(30) @ Matrix.scale(2, 3)
    assert (m @ m.inverse()).isclose(IDENTITY)
    assert m.determinant == pytest.approx(6)
    with pytest.raises(ValueError):
        Matrix.scale(0).inverse()


def test_skew() -> None:
    assert Matrix.skew_x(45).c == pytest.approx(1.0)
    assert Matrix.skew_y(45).b == pytest.approx(1.0)


def test_simplified_and_concat() -> None:
    t = Transform().translate(1, 2) @ Transform().scale(3)
    assert str(t) == "translate(1 2) scale(3)"
    simple = t.simplified()
    assert str(simple) == "matrix(3 0 0 3 1 2)"
    assert simple.to_matrix().isclose(t.to_matrix())
    assert IDENTITY.is_identity


def test_as_transform() -> None:
    assert as_transform("rotate(5)") == Transform([Rotate(5)])
    assert as_transform(Rotate(5)) == Transform([Rotate(5)])
    assert str(as_transform(Matrix())) == "matrix(1 0 0 1 0 0)"


def test_op_arguments_drop_defaults() -> None:
    assert str(Translate(5)) == "translate(5)"
    assert str(Scale(2, 3)) == "scale(2 3)"
    assert str(Rotate(10, 1, 2)) == "rotate(10 1 2)"
    assert Rotate(90).to_matrix().apply(1, 0) == pytest.approx(Point(0, 1))
    assert math.isclose(SkewX(0).to_matrix().c, 0)


class TestPointArithmetic:
    def test_vector_ops_broadcast_like_numpy(self) -> None:
        import numpy as np

        p = Point(1, 2)
        assert p + Point(3, 4) == (4, 6) and p - (1, 1) == (0, 1) and (5, 5) - p == (4, 3)
        assert p * 2 == (2, 4) and 2 * p == (2, 4) and p * (2, 3) == (2, 6) and p / 2 == (0.5, 1)
        assert p + 1 == (2, 3)
        assert np.asarray(p).tolist() == [1.0, 2.0]
        assert (np.array([1.0, 1.0]) + np.asarray(p)).tolist() == [2.0, 3.0]

    def test_position_plus_offset(self) -> None:
        import svgwriter as svg

        r = svg.rect(0, 0, 10, 10)
        assert r.position + (5, 0) == (10, 5)

    def test_bad_operand(self) -> None:
        with pytest.raises(TypeError, match="pair"):
            Point(1, 2) + "ab"  # type: ignore[operator]


class TestReadableTransformText:
    def test_rotation_pivot_outside_element_uses_its_anchor(self) -> None:
        import svgwriter as svg

        circle = svg.circle(50, 50, 10).translate(20, 0).rotate(45)
        assert 'transform="translate(20) rotate(45 50 50)"' in str(circle)

    def test_rotation_inside_element_stays_short(self) -> None:
        import svgwriter as svg

        assert 'transform="rotate(30 5 5)"' in str(svg.rect(0, 0, 10, 10).rotate(30))

    def test_text_round_trips_to_same_matrix(self) -> None:
        import svgwriter as svg

        circle = svg.circle(50, 50, 10).translate(20, 0).rotate(45)
        again = svg.parse(f'<svg xmlns="http://www.w3.org/2000/svg">{circle}</svg>')[0]
        assert svg.Transform.parse(again.get("transform")).to_matrix().as_tuple() == pytest.approx(
            circle.t.as_tuple(), abs=1e-3)

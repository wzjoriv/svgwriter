import warnings

import pytest

import svgwriter as svg
from svgwriter.ops import intersection, union


@pytest.fixture
def squares():
    return svg.path("M0 0 H10 V10 H0 Z"), svg.path("M5 0 H15 V10 H5 Z")


class TestOpenPaths:
    @pytest.mark.parametrize("operator", ["__or__", "__and__", "__sub__", "__xor__"])
    def test_empty_results_from_open_paths_warn(self, operator):
        with pytest.warns(UserWarning, match="open path"):
            result = getattr(svg.line(0, 0, 10, 10), operator)(svg.line(0, 10, 10, 0))
        assert len(result.d) == 0

    def test_union_of_many_and_function_api_warn(self):
        with pytest.warns(UserWarning, match="union is empty"):
            union("M0 0 L10 0", "M0 5 L10 5")
        with pytest.warns(UserWarning, match="intersection is empty"):
            intersection("M0 0 L10 10", "M0 0 H10 V10 H0 Z")

    def test_closed_or_non_empty_results_stay_quiet(self, squares):
        a, b = squares
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert len((a - a).d) == 0
            assert (svg.polyline([(0, 0), (10, 0), (10, 10)]) | b).exact_bbox().width == 15
        with pytest.warns(UserWarning, match="stroked"):
            svg.line(0, 0, 10, 0) | svg.line(0, 1, 10, 1)
        assert (svg.line(0, 0, 10, 0, stroke_width=2).stroked() | b).exact_bbox().width == 15


class TestJoinVersusUnion:
    def test_plus_keeps_both_subpaths_and_the_fill_rule_decides(self, squares):
        a, b = squares
        joined = a + b
        assert str(joined.d) == "M0 0 H10 V10 H0 Z M5 0 H15 V10 H5 Z"
        assert joined.contains_point(7, 5)
        joined.set("fill-rule", "evenodd")
        assert not joined.contains_point(7, 5) and joined.contains_point(2, 5)

    def test_or_is_the_true_union_under_both_rules(self, squares):
        a, b = squares
        for rule in ("nonzero", "evenodd"):
            merged = (a | b).update(fill_rule=rule)
            assert len(merged.d.subpaths()) == 1
            assert merged.contains_point(7, 5) and merged.contains_point(2, 5) and merged.contains_point(13, 5)

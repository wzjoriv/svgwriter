from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.attributes.cascade import computed, matches, resolve_styles
from svgwriter.attributes.rules import parse_css


def tree() -> tuple[svg.Svg, svg.Group, svg.Rect]:
    root = svg.Svg()
    g = root.append(svg.Group(id="outer", class_="box", fill="blue", font_size=20))
    r = g.append(svg.Rect(id="r", class_="a b", data_kind="x"))
    return root, g, r


class TestParse:
    def test_rules_comments_groups_important_and_at_rules(self) -> None:
        rules = parse_css("@import url(x.css); /* c */ rect, .a { fill: red; stroke: blue !important } @media print { g{} }")
        assert [r.selector for r in rules] == ["rect", ".a"]
        assert rules[0].declarations == (("fill", "red", False), ("stroke", "blue", True))

    def test_specificity(self) -> None:
        (rule,) = parse_css("g#x.a > rect[fill] { fill: red }")
        assert rule.specificity == (1, 2, 2)


class TestMatching:
    @pytest.mark.parametrize(
        ("selector", "expected"),
        [("rect", True), ("*", True), (".a", True), (".a.b", True), (".c", False), ("#r", True),
         ("rect#r.a", True), ("g rect", True), ("g > rect", True), ("svg > rect", False), ("svg rect", True),
         ("#outer .b", True), ("[data-kind]", True), ('[data-kind="x"]', True), ("[data-kind=y]", False),
         ("[class~=b]", True), ("rect:first-child", True), ("rect:hover", False), ("circle", False)],
    )
    def test_selectors(self, selector: str, expected: bool) -> None:
        _, _, r = tree()
        assert matches(r, selector) is expected


class TestComputed:
    def test_inheritance_and_non_inherited(self) -> None:
        _, g, r = tree()
        g.set("opacity", 0.5)
        assert r.computed("fill") == "blue" and r.computed("font_size") == 20 and r.computed("opacity") is None

    def test_precedence_inline_over_css_over_attribute(self) -> None:
        root, _, r = tree()
        root.append(svg.StyleElement("rect { fill: green } #r { stroke: red } .a { stroke: lime }"))
        assert r.computed("fill") == "green" and r.computed("stroke") == "red"
        r.set("fill", "orange")
        assert r.computed("fill") == "green"
        r.style = {"fill": "purple"}
        assert r.computed("fill") == "purple"

    def test_important_wins_over_specificity(self) -> None:
        root, _, r = tree()
        root.append(svg.StyleElement(".a { fill: red !important } #r { fill: green }"))
        assert r.computed("fill") == "red"

    def test_inherit_keyword_for_non_inherited_property(self) -> None:
        _, g, r = tree()
        g.set("opacity", 0.3)
        r.set("opacity", "inherit")
        assert r.computed("opacity") == 0.3

    def test_default(self) -> None:
        assert svg.Rect().computed("stroke", "none") == "none"


def test_resolve_styles_bakes_css_into_attributes() -> None:
    root, _, r = tree()
    root.append(svg.StyleElement("rect { fill: green; stroke-width: 3 }"))
    r.style = {"stroke": "red"}
    resolve_styles(root)
    assert r.get("fill") == "green" and r.get("stroke") == "red" and not r.has("style")


@pytest.mark.parametrize(("selector", "expected"), [
    ("ellipse + circle", ["c1", "c2"]), ("circle + ellipse.b", []), ("g rect + circle", []),
    ("g > ellipse ~ circle", ["c1", "c2"]), ("svg g circle", ["c0", "c1", "c2"]), ('[class~="b"] + circle', ["c2"]),
])
def test_sibling_combinators_and_backtracking(selector, expected):
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg"><g><circle id="c0"/><ellipse class="a"/><circle id="c1"/>'
        '<ellipse class="a b"/><circle id="c2"/></g></svg>')
    assert [e.id for e in doc.root.iter("circle") if matches(e, selector)] == expected


def test_resolved_sheets_are_removed_so_inline_values_keep_winning():
    root = svg.Svg(svg.StyleElement(".a { fill: blue }"), svg.Rect(class_="a", style="fill:red"))
    resolve_styles(root)
    rect = root.find(svg.Rect)
    assert rect.get("fill") == "red" and root.find(svg.StyleElement) is None
    assert computed(rect, "fill") == "red"

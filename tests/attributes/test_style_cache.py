from __future__ import annotations

import svgwriter as svg
from svgwriter.model.attributes.cascade import computed
from svgwriter.model.attributes.rules import parse_css, rule_set, set_class_rules


def styled(css: str) -> tuple[svg.Svg, svg.Group, svg.Rect]:
    root = svg.Svg()
    root.append(svg.StyleElement(css))
    group = root.append(svg.Group(class_="box"))
    rect = group.append(svg.Rect(0, 0, 1, 1, class_="a"))
    return root, group, rect


class TestInvalidation:
    def test_class_change(self) -> None:
        _, _, rect = styled(".a { fill: red } .b { fill: blue }")
        assert rect.computed("fill") == "red"
        rect.set("class", "b")
        assert rect.computed("fill") == "blue"
        rect.set("class", None)
        assert rect.computed("fill") is None

    def test_id_and_attribute_change(self) -> None:
        _, _, rect = styled("#r { fill: red } [data-k=x] { stroke: blue }")
        assert rect.computed("fill") is None and rect.computed("stroke") is None
        rect.set("id", "r")
        rect.set("data-k", "x")
        assert rect.computed("fill") == "red" and rect.computed("stroke") == "blue"
        rect.set("data-k", "y")
        assert rect.computed("stroke") is None

    def test_style_rule_change(self) -> None:
        root, _, rect = styled(".a { fill: red }")
        assert rect.computed("fill") == "red"
        sheet = next(root.iter("style"))
        sheet.children[:] = [".a { fill: green }"]
        assert rect.computed("fill") == "green"
        root.append(svg.StyleElement(".a { fill: navy }"))
        assert rect.computed("fill") == "navy"

    def test_inline_style_change(self) -> None:
        _, _, rect = styled(".a { fill: red }")
        rect.style = "fill: lime"
        assert rect.computed("fill") == "lime"
        rect.style = {"fill": "teal"}
        assert rect.computed("fill") == "teal"

    def test_ancestor_class_change(self) -> None:
        _, group, rect = styled(".box .a { fill: red } .other .a { fill: blue }")
        assert rect.computed("fill") == "red"
        group.set("class", "other")
        assert rect.computed("fill") == "blue"

    def test_inserted_element(self) -> None:
        _, group, rect = styled(".a:first-child { fill: red } circle + .a { stroke: blue }")
        assert rect.computed("fill") == "red" and rect.computed("stroke") is None
        group.insert(0, svg.Circle(r=1))
        assert rect.computed("fill") is None and rect.computed("stroke") == "blue"

    def test_moved_under_new_ancestor(self) -> None:
        root, group, rect = styled(".wrap .a { fill: red }")
        assert rect.computed("fill") is None
        wrap = root.append(svg.Group(class_="wrap"))
        group.remove(rect)
        wrap.append(rect)
        assert rect.computed("fill") == "red"

    def test_class_rules_change(self) -> None:
        root = svg.Svg()
        rect = root.append(svg.Rect(0, 0, 1, 1, class_="a"))
        set_class_rules(root, {"a": parse_css(".a { fill: red }")})
        assert computed(rect, "fill") == "red"
        set_class_rules(root, {"a": parse_css(".a { fill: blue }")})
        assert computed(rect, "fill") == "blue"

    def test_theme_change(self) -> None:
        doc = svg.Document(10, 10)
        rect = doc.rect(0, 0, 1, 1).as_role("surface")
        light = rect.computed("fill")
        doc.theme = "dark"
        assert rect.computed("fill") != light
        doc.theme = "light"
        assert rect.computed("fill") == light


class TestSharing:
    def test_equal_rules_share_one_index(self) -> None:
        assert rule_set(parse_css(".a { fill: red }")) is rule_set(parse_css(".a { fill: red }"))

    def test_index_keeps_cascade_order(self) -> None:
        _, _, rect = styled("rect { fill: red } .a { fill: blue } * { fill: green !important }")
        assert rect.computed("fill") == "green"

    def test_text_measure_follows_edits(self) -> None:
        label = svg.text("8", font_size=10)
        stack = svg.VStack(label)
        small = stack.bounds().height
        label.set("font-size", 40)
        assert stack.bounds().height > small

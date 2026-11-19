from __future__ import annotations

from pathlib import Path

import pytest

import svgwriter as svg


class TestDocument:
    def test_group_context_manager_nests(self) -> None:
        doc = svg.Document(100, 100)
        with doc.group(fill="red") as outer:
            doc.add(svg.Rect())
            with doc.group(id="inner") as inner:
                doc.add(svg.Circle())
            doc.add(svg.Line())
        doc.add(svg.Ellipse())
        assert [c.tag for c in outer] == ["rect", "g", "line"]
        assert [c.tag for c in inner] == ["circle"]
        assert doc.current is doc.root
        assert [c.tag for c in doc.root] == ["g", "ellipse"]

    def test_stack_unwinds_on_error(self) -> None:
        doc = svg.Document(10, 10)
        with pytest.raises(RuntimeError), doc.group():
            raise RuntimeError
        assert doc.current is doc.root

    def test_nest_any_container(self) -> None:
        doc = svg.Document(10, 10)
        with doc.nest(svg.A(href="https://example.org")) as link:
            doc.add(svg.Text("go"))
        assert len(link) == 1

    def test_define_title_describe(self) -> None:
        doc = svg.Document(10, 10)
        grad = doc.define(svg.RadialGradient())
        doc.title("T")
        doc.describe("D")
        assert grad.id and grad.parent is doc.defs
        assert doc.root[0].tag == "title"
        assert doc.get_element_by_id(grad.id) is grad
        assert len(list(doc.root.iter())) == 5 and len(doc) == 0

    def test_writing_context_manager(self, tmp_path: Path) -> None:
        target = tmp_path / "w.svg"
        with svg.Document.writing(target, 20, 20, options=svg.SerializeOptions(pretty=False)) as doc:
            doc.add(svg.Rect(1, 1, 2, 2))
        text = target.read_text(encoding="utf-8")
        assert text.count("\n") == 1
        assert svg.Document.open(target).root.find(svg.Rect) is not None

    def test_from_string_requires_svg_root(self) -> None:
        with pytest.raises(ValueError):
            svg.Document.from_string("<rect/>")
        doc = svg.Document.from_string(svg.Document(5, 5).to_string())
        assert doc.root.view_box == svg.ViewBox(0, 0, 5, 5)

    def test_size_without_view_box(self) -> None:
        doc = svg.Document(width=10)
        assert doc.root.get("width") == 10 and doc.root.view_box is None

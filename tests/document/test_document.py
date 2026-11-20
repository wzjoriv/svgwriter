from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg


class Foreign:
    """Stands in for a plot or diagram object from another library."""

    def _repr_svg_(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10" version="1.1"><rect width="20" height="10" fill="red"/></svg>'


class TestAccess:
    def test_index_slice_id_iteration(self) -> None:
        doc = svg.Document(100, 100)
        doc.title("T")
        doc.define(svg.LinearGradient(id="g"))
        a = doc.rect(0, 0, 1, 1, id="logo")
        b = doc.circle(5, 5, 1)
        assert doc[0] is a and doc[-1] is b and doc[0:2] == [a, b] and list(doc) == [a, b] and len(doc) == 2
        assert doc["logo"] is a and doc["g"].tag == "linearGradient"
        assert "logo" in doc and a in doc and "nope" not in doc and svg.Rect() not in doc

    def test_errors(self) -> None:
        doc = svg.Document(10, 10)
        with pytest.raises(KeyError, match="nope"):
            _ = doc["nope"]
        with pytest.raises(IndexError):
            _ = doc[0]


class TestIngest:
    def test_repr_svg_objects_become_nested_svg(self) -> None:
        doc = svg.Document(100, 100)
        nested = doc.add(Foreign())
        doc += Foreign()
        assert isinstance(nested, svg.Group) and isinstance(nested[0], svg.Svg) and len(doc) == 2
        assert nested.parent is doc.root and not nested[0].has("version") and nested.find(svg.Rect) is not None
        pixels = doc.rasterize()
        assert np.allclose(pixels[5, 5], (1, 0, 0, 1))

    def test_ingest_moves_with_transforms(self) -> None:
        doc = svg.Document(100, 100)
        doc.add(Foreign()).translate(50, 50)
        assert np.allclose(doc.rasterize()[55, 55], (1, 0, 0, 1))

    def test_empty_repr(self) -> None:
        class Empty:
            def _repr_svg_(self) -> None:
                return None

        with pytest.raises(TypeError, match="no SVG"):
            svg.Document(10, 10).add(Empty())


class TestAutoSize:
    def test_size_follows_content(self) -> None:
        doc = svg.Document()
        doc.rect(10, 20, 30, 40, fill="red")
        doc.circle(100, 100, 10).translate(5, 0)
        assert doc.auto_size
        text = doc.to_string()
        assert 'viewBox="10 20 105 90"' in text and 'width="105"' in text
        assert not doc.root.has("viewBox")
        assert doc.rasterize().shape == (90, 105, 4)

    def test_stroke_and_fit(self) -> None:
        doc = svg.Document()
        doc.rect(0, 0, 10, 10, stroke="black", stroke_width=2)
        assert doc.content_bounds() == (-1, -1, 12, 12)
        doc.fit(padding=1)
        assert not doc.auto_size and doc.root.view_box == (-2, -2, 14, 14)

    def test_explicit_size_wins_and_empty_document(self) -> None:
        assert not svg.Document(5, 5).auto_size
        assert svg.Document().content_bounds() is None and "viewBox" not in svg.Document().to_string()


class TestNotebook:
    def test_repr_svg_and_png(self) -> None:
        doc = svg.Document()
        doc.circle(5, 5, 5, fill="blue")
        assert doc._repr_svg_().startswith("<svg") and "viewBox" in doc._repr_svg_()
        assert doc._repr_png_()[:4] == bytes.fromhex("89504e47")


def test_save_auto_sized(tmp_path) -> None:
    doc = svg.Document()
    doc.rect(0, 0, 7, 3)
    doc.save(tmp_path / "x.svg")
    assert 'viewBox="0 0 7 3"' in (tmp_path / "x.svg").read_text()


def test_documents_embed_as_a_placeable_nested_svg_copy():
    import svgwriter as svg

    inner = svg.Document(50, 50)
    rect = inner.rect(0, 0, 50, 50, fill="red")
    outer = svg.Document(200, 100)
    holder = outer.add(inner).place(100, 50)
    rect.set("fill", "blue")
    assert holder.tag == "g" and holder[0].tag == "svg" and holder[0].get("version") is None
    assert outer.rasterize()[50, 100].round(2).tolist() == [1, 0, 0, 1]

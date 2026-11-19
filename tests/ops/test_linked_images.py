from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg

BLUE = (0.0, 0.0, 1.0)


def write_png(path, color=BLUE) -> None:
    path.write_bytes(svg.Image(np.tile(color, (4, 4, 1))).encode("png"))


def page(href: str, **group) -> str:
    doc = svg.Document(8, 8)
    doc.group(**group).add(svg.Image(href, 0, 0, 8, 8))
    return doc.to_string()


def test_relative_link_resolves_against_the_file(tmp_path) -> None:
    (tmp_path / "img").mkdir()
    write_png(tmp_path / "img" / "a.png")
    (tmp_path / "doc.svg").write_text(page("img/a.png"), encoding="utf-8")
    pixels = svg.Document.open(tmp_path / "doc.svg").rasterize()
    assert np.allclose(pixels[4, 4], (*BLUE, 1), atol=0.02)


def test_xml_base_on_ancestor(tmp_path) -> None:
    (tmp_path / "assets").mkdir()
    write_png(tmp_path / "assets" / "b.png")
    (tmp_path / "doc.svg").write_text(page("b.png", xml_base="assets/"), encoding="utf-8")
    assert svg.Document.from_file(tmp_path / "doc.svg").rasterize()[4, 4, 3] == pytest.approx(1)


def test_linked_svg_renders(tmp_path) -> None:
    inner = svg.Document(4, 4)
    inner.rect(0, 0, 4, 4, fill="lime")
    inner.save(tmp_path / "inner.svg")
    (tmp_path / "doc.svg").write_text(page("inner.svg"), encoding="utf-8")
    assert np.allclose(svg.Document.open(tmp_path / "doc.svg").rasterize()[4, 4], (0, 1, 0, 1), atol=0.02)


def test_missing_and_remote_links_are_skipped_and_document_unchanged(tmp_path) -> None:
    (tmp_path / "doc.svg").write_text(page("missing.png"), encoding="utf-8")
    doc = svg.Document.open(tmp_path / "doc.svg")
    assert doc.rasterize()[..., 3].max() == 0
    remote = svg.Document.from_string(page("https://example.org/x.png"))
    assert remote.rasterize()[..., 3].max() == 0 and remote.root.find(svg.Image).pixels is None


def test_links_relative_to_cwd_for_documents_built_in_code(tmp_path, monkeypatch) -> None:
    write_png(tmp_path / "c.png")
    monkeypatch.chdir(tmp_path)
    doc = svg.Document(8, 8)
    doc.add(svg.Image("c.png", 0, 0, 8, 8))
    assert doc.rasterize()[4, 4, 3] == pytest.approx(1) and doc[0].pixels is None

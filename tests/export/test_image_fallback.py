import zipfile

import pytest

import svgwriter as svg

pytest.importorskip("pptx")


def _doc() -> svg.Document:
    doc = svg.Document(width=200, height=100)
    doc.rect(10, 10, 80, 50, rx=8, fill="teal", filter=svg.filters.drop_shadow())
    doc.circle(150, 50, 25, fill="gold")
    return doc


def _slide(path) -> str:
    return zipfile.ZipFile(path).read("ppt/slides/slide1.xml").decode()


def test_filtered_elements_become_pictures_and_the_rest_stays_shapes(tmp_path):
    path = tmp_path / "deck.pptx"
    with pytest.warns(UserWarning, match="drawn as images"):
        _doc().save(path)
    xml = _slide(path)
    assert xml.count("<p:pic>") == 1 and xml.count("<p:sp>") == 1


def test_drop_keeps_shapes_without_the_effect(tmp_path):
    path = tmp_path / "deck.pptx"
    with pytest.warns(UserWarning, match="skipped: filter"):
        _doc().save(path, fallback="drop")
    xml = _slide(path)
    assert "<p:pic>" not in xml and xml.count("<p:sp>") == 2


def test_word_takes_the_same_fallback(tmp_path):
    pytest.importorskip("docx")
    path = tmp_path / "page.docx"
    with pytest.warns(UserWarning, match="drawn as images"):
        _doc().save(path, dpi=96)
    assert b"word/media/" in zipfile.ZipFile(path).read("[Content_Types].xml") or \
        any(name.startswith("word/media/") for name in zipfile.ZipFile(path).namelist())

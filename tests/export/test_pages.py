import io

import pytest

import svgwriter as svg


def _pages():
    first = svg.Document(200, 100)
    first.rect(0, 0, 200, 100, fill="red")
    second = svg.Document(100, 50)
    second.circle(50, 25, 20, fill="blue")
    return [first, second]


def test_pdf_writes_one_page_per_document_with_its_own_size():
    data = svg.export.export(_pages(), "pdf")
    back = svg.export.find_importer("pdf").function(data, page=None)
    assert [(p.root.get("width"), p.root.get("height")) for p in back] == [(200.0, 100.0), (100.0, 50.0)]
    assert back[0][0].get("fill") == "#ff0000"
    assert svg.export.find_importer("pdf").function(data, page=1).root.get("width") == 100.0


def test_single_document_list_and_tuple_are_accepted():
    assert svg.export.export((svg.Document(5, 5),), "pdf")[:5] == b"%PDF-"


def test_single_page_formats_refuse_lists():
    with pytest.raises(ValueError, match="multi-page"):
        svg.export.export(_pages(), "png")
    with pytest.raises(ValueError, match="no documents"):
        svg.export.export([], "pdf")


def test_save_and_open_all(tmp_path):
    path = svg.export.save(_pages(), tmp_path / "pages.pdf")
    pages = svg.Document.open_all(path)
    assert len(pages) == 2
    assert all(page.root._source_path == str(path) for page in pages)
    assert len(svg.Document.open_all(svg.export.save(svg.Document(4, 4), tmp_path / "one.svg"))) == 1
    with pytest.raises(ValueError, match="open_all"):
        svg.Document.open(path, page=None)


def test_time_applies_to_every_page():
    doc = svg.Document(100, 20)
    ball = doc.circle(10, 10, 5, fill="red")
    ball.append(svg.Animate(attribute_name="cx", from_=10, to=90, dur=2))
    back = svg.export.find_importer("pdf").function(svg.export.export([doc, doc], "pdf", seconds=1.0), page=None)
    assert all(page[0].bounds().x == pytest.approx(45, abs=1) for page in back)


def test_registry_flags():
    assert svg.export.exporters()["pdf"].multipage and not svg.export.exporters()["svg"].multipage
    assert svg.export.importers()["pptx"].page_option == "slide"
    assert svg.export.importers()["svg"].page_option is None


def test_pptx_one_slide_per_document_centred_on_the_largest_size():
    pptx = pytest.importorskip("pptx")
    data = svg.export.export(_pages(), "pptx")
    deck = pptx.Presentation(io.BytesIO(data))
    assert len(deck.slides) == 2
    assert (deck.slide_width, deck.slide_height) == (200 * 9525, 100 * 9525)
    circle = next(iter(deck.slides[1].shapes))
    assert (circle.left, circle.top) == ((50 + 30) * 9525, (25 + 5) * 9525)
    back = svg.export.find_importer("pptx").function(data, slide=None)
    assert len(back) == 2 and back[1][0].bounds().x == pytest.approx(80, abs=0.5)
    assert svg.export.find_importer("pptx").function(data).root.get("width") == 200.0


def test_pptx_open_all(tmp_path):
    pytest.importorskip("pptx")
    path = svg.export.save(_pages(), tmp_path / "deck.pptx")
    assert len(svg.Document.open_all(path)) == 2

import pytest

import svgwriter as svg


def _doc():
    doc = svg.Document(40, 20)
    doc.title("Demo page")
    doc.rect(0, 0, 40, 20, id="box", fill="teal")
    return doc


def test_page_embeds_static_svg_and_binds_handlers_in_the_page():
    page = svg.export.export(_doc(), "html", handlers={"box": {"click": "this.style.fill = 'red'"}}, css="#box{}")
    assert page.startswith("<!doctype html>") and "<title>Demo page</title>" in page
    svg_part = page[page.index("<svg"):page.index("</svg>")]
    assert "onclick" not in svg_part and "addEventListener" in page and "#box{}" in page


def test_handlers_must_name_existing_ids():
    with pytest.raises(ValueError, match="nope"):
        svg.export.export(_doc(), "html", handlers={"nope": {"click": ""}})


def test_html_round_trip_reads_the_inline_svg(tmp_path):
    target = svg.export.save(_doc(), tmp_path / "page.html")
    back = svg.Document.open(target)
    assert [e.tag for e in back] == ["rect"] and back["box"].get("fill") == "teal"


def test_script_end_tags_in_handlers_are_escaped():
    page = svg.export.export(_doc(), "html", handlers={"box": {"click": "x = '</script>'"}})
    assert page.count("</script>") == 1

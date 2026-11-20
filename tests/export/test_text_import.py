import svgwriter as svg
from svgwriter.export._text import read_markdown, read_text


def test_plain_text_keeps_lines_and_spaces():
    doc = read_text(b"a  b\n\nc")
    lines = [t.text_content for t in doc[0]]
    assert lines == ["a  b", "c"] and doc[0][0].get("xml:space") == "preserve"


def test_markdown_structure():
    md = b"# Title\n\nSome **bold** and `code`\n\n- one\n  - two\n1. first\n\n```\nx = 1\n```\n"
    texts = list(read_markdown(md)[0])
    assert texts[0].text_content == "Title" and texts[0].get("font-weight") == "bold"
    assert texts[1].text_content == "Some bold and code" and texts[1].children[1].get("font-weight") == "bold"
    assert texts[2].text_content.startswith("• ") and texts[3].get("x") > texts[2].get("x")
    assert texts[4].text_content == "1. first" and texts[5].get("font-family") == "monospace"


def test_extensions_route(tmp_path):
    target = tmp_path / "notes.md"
    target.write_text("# Hi", encoding="utf-8")
    assert svg.Document.open(target)[0][0].text_content == "Hi"
    assert svg.export.find_importer("x.txt").name == "text"


def test_generic_families_resolve_to_real_fonts():
    from svgwriter.ops._fonts import resolve_font

    mono = resolve_font("monospace", 12, "normal", False)
    assert mono.measureText("iiii") == mono.measureText("WWWW")

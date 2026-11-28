from types import SimpleNamespace

from svgwriter.formats.export._vector import _pdf_content


def _painter():
    return SimpleNamespace(objects={})


def test_type3_fonts_take_family_and_weight_from_their_descriptor():
    font = {"Subtype": "/Type3", "FontDescriptor": {
        "FontName": "/AAAAAA+SvgwNoSuchSans-Bold", "FontFamily": b"Svgw No Such Sans", "FontWeight": 700,
        "ItalicAngle": 0}}
    family, bold, italic = _pdf_content._described(_painter(), font)
    assert family == "Svgw No Such Sans" and bold and not italic


def test_descriptor_without_family_falls_back_to_the_font_name():
    font = {"FontDescriptor": {"FontName": "/BAAAAA+SvgwSerif-Italic", "ItalicAngle": -12}}
    family, bold, italic = _pdf_content._described(_painter(), font)
    assert "Svgw" in family and not bold and italic

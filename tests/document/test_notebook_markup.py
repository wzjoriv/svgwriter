import re

import svgwriter as svg
from svgwriter._internal._drawable import notebook_markup


def _drawing(color: str) -> svg.Document:
    doc = svg.Document(width=40, height=20)
    doc.rect(0, 0, 40, 20, fill=svg.LinearGradient.horizontal(color, "white"))
    dot = doc.circle(10, 10, 4, id="dot")
    dot.animate.fade_in(1)
    doc.circle(30, 10, 4).append(svg.Animate(attribute_name="r", from_=4, to=8, dur="1s", begin="dot.end"))
    return doc


def test_two_drawings_on_one_page_share_no_ids():
    first, second = _drawing("red")._repr_svg_(), _drawing("blue")._repr_svg_()
    assert not set(re.findall(r'id="([^"]+)"', first)) & set(re.findall(r'id="([^"]+)"', second))


def test_every_reference_follows_its_id():
    markup = _drawing("red")._repr_svg_()
    ids = set(re.findall(r'id="([^"]+)"', markup))
    assert set(re.findall(r"url\(#([^)]+)\)", markup)) <= ids
    assert re.search(r'begin="(s[0-9a-f]+-dot)\.end"', markup)


def test_saved_files_keep_their_ids():
    doc = _drawing("red")
    assert 'id="dot"' in doc.to_string() and 'id="dot"' not in doc._repr_svg_()


def test_markup_without_ids_is_only_made_ascii():
    assert notebook_markup('<svg><text>é</text></svg>') == "<svg><text>&#233;</text></svg>"

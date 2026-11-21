from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.attributes.cascade import resolve_styles


@pytest.mark.parametrize("css, expected", [("stroke-width: 20PX", "20px"), ("stroke-width: 1.5Em", "1.5em"),
                                           ("stroke-width: 3", "3")])
def test_css_units_are_case_insensitive(css: str, expected: str) -> None:
    doc = svg.parse(f'<svg xmlns="http://www.w3.org/2000/svg"><rect style="{css}"/></svg>')
    resolve_styles(doc)
    assert next(doc.iter("rect")).attributes["stroke-width"] == expected


def test_marker_shorthand_expands_to_longhands() -> None:
    doc = svg.parse('<svg xmlns="http://www.w3.org/2000/svg"><path style="marker: url(#m)"/></svg>')
    resolve_styles(doc)
    path = next(doc.iter("path"))
    assert [path.attributes[name] for name in ("marker-start", "marker-mid", "marker-end")] == ["url(#m)"] * 3

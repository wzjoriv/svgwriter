import numpy as np
import pytest

import svgwriter as svg


def test_hover_rules_are_written_while_saving_only():
    doc = svg.Document(width=40, height=20)
    button = doc.rect(0, 0, 40, 20, fill="teal").on_hover(fill="tomato")
    text = doc.to_string()
    assert f"#{button.id}:hover {{ fill:tomato !important }}" in text
    assert all(child.get("id") != "svgwriter-hover" for child in doc.root.children)


def test_hover_beats_roles_and_still_output_shows_the_resting_state():
    doc = svg.Document(width=40, height=20)
    doc.rect(0, 0, 40, 20, fill="#008080").as_role("box").on_hover(fill="#ff0000")
    assert np.asarray(doc.rasterize())[5, 5, 0] == 0


def test_calls_add_to_the_hover_style_and_clones_keep_their_own():
    one = svg.circle(0, 0, 5).on_hover(fill="red")
    two = one.clone().on_hover(stroke="blue")
    doc = svg.Document(width=20, height=20)
    doc += one
    assert "stroke:blue" not in doc.to_string()
    one.on_hover(opacity=0.5)
    assert "fill:red !important;opacity:0.5 !important" in doc.to_string()
    assert two is not one


def test_geometry_cannot_change_on_hover():
    with pytest.raises(ValueError, match="not a presentation property"):
        svg.circle(0, 0, 5).on_hover(r=8)

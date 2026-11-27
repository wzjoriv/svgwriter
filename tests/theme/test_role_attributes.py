import svgwriter as svg


def _theme():
    return svg.themes.get("light").replace(name="cards", roles={"card": {"fill": "#eeeeee", "rx": "6", "ry": "4"}})


def test_role_geometry_is_written_as_attributes_not_css():
    doc = svg.Document(width=100, height=60, theme=_theme())
    card = doc.rect(10, 10, 50, 30)
    card.as_role("card")
    text = doc.to_string()
    assert 'rx="6"' in text and 'ry="4"' in text
    assert "rx:" not in text and "ry:" not in text
    assert "rx" not in card.attributes


def test_attributes_set_on_the_element_win():
    doc = svg.Document(width=100, height=60, theme=_theme())
    card = doc.rect(10, 10, 50, 30, rx=2)
    card.as_role("card")
    assert 'rx="2"' in doc.to_string()


def test_role_geometry_renders():
    np = __import__("numpy")
    doc = svg.Document(width=100, height=60, theme=_theme())
    doc.rect(10, 10, 50, 30).as_role("card")
    assert np.asarray(doc.rasterize())[10, 10, 3] == 0


def test_attributes_lists_only_geometry():
    assert _theme().attributes("card") == {"rx": "6", "ry": "4"}

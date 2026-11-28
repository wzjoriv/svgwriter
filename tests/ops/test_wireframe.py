import svgwriter as svg


def _doc():
    doc = svg.Document(width=120, height=60)
    doc.rect(5, 5, 40, 30, fill="crimson", filter=svg.filters.drop_shadow(), opacity=0.5).as_role("box")
    doc.add(svg.Image(svg.Pixels.solid(4, 4, "teal").rgba(), 60, 5, 20, 20)) if hasattr(svg, "Pixels") else None
    doc.text("Hi", x=60, y=50, font_size=14).animate.fade_in()
    return doc


def test_shapes_become_outlines_and_the_original_is_kept():
    doc = _doc()
    wire = doc.wireframe(color="#123456", width=2)
    rect = wire.root.find("rect")
    assert rect.style["fill"] == "none" and rect.style["stroke"] == "#123456" and rect.style["stroke-width"] == "2px"
    assert rect.get("filter") is None and rect.get("opacity") is None
    assert doc.root.find("rect").get("fill") == "crimson"


def test_text_keeps_its_size_and_animations_are_left_out():
    wire = _doc().wireframe()
    text = wire.root.find("text")
    assert text.get("font-size") == 14 or str(text.get("font-size")) == "14"
    assert "<animate" not in wire.to_string()


def test_bounds_add_dashed_boxes_beside_shapes():
    wire = _doc().wireframe(bounds=True)
    dashed = [e for e in wire.root.iter() if e.tag == "rect" and e.get("stroke-dasharray")]
    assert dashed


def test_default_width_scales_with_the_page():
    page = svg.Document(size="a4")
    page.rect(10, 10, 50, 50)
    assert float(page.wireframe().root.find("rect").style["stroke-width"].rstrip("px")) < 1

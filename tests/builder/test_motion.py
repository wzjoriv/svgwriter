import pytest

import svgwriter as svg
from svgwriter.catalog.builder import star


def _opacity_at(doc, time):
    return float(doc.at(time)[0].get("opacity"))


def test_fades_and_chaining():
    doc = svg.Document(20, 20)
    box = doc.rect(0, 0, 10, 10)
    box.animate.fade_in(1).fade_out(1, begin=2)
    assert _opacity_at(doc, 0.5) == pytest.approx(0.5) and _opacity_at(doc, 2.5) == pytest.approx(0.5)


def test_draw_reveals_the_stroke():
    doc = svg.Document(40, 40)
    doc.circle(20, 20, 10, fill="none", stroke="black").animate.draw(1)
    start, end = (float(doc.at(t)[0].get("stroke-dashoffset")) for t in (0, 1))
    assert start == pytest.approx(62.83, abs=0.1) and end == 0


def test_spin_grow_and_slide_end_where_they_should():
    doc = svg.Document(100, 100)
    shape = doc.add(star(50, 50, 20))
    shape.animate.spin(1).grow(1)
    assert doc.at(1)[0].bounds() == pytest.approx(shape.bounds(), abs=0.01)
    slider = doc.rect(10, 10, 10, 10)
    slider.animate.slide_in("left", 1, distance=50)
    assert doc.at(0)[1].bounds().x == pytest.approx(-40) and doc.at(1)[1].bounds().x == pytest.approx(10)


def test_typewriter_wipe_morph_and_stagger():
    doc = svg.Document(200, 60)
    doc.text("abcd", x=0, y=20).animate.typewriter(1)
    visible = [s.get("visibility") for s in doc.at(0.5)[0].children]
    assert visible == ["visible", "visible", "visible", "hidden"]
    doc.rect(50, 0, 40, 40).animate.wipe("left", 1)
    path = doc.path().move_to(100, 0).line_to(140, 0).line_to(140, 40).close()
    path.animate.morph(svg.circle(170, 20, 15), 1)
    assert doc.at(1)[2].bounds() == pytest.approx((155, 5, 30, 30), abs=0.5)
    row = doc.group(*[svg.rect(i * 10, 50, 5, 5) for i in range(3)])
    row.animate.stagger("fade_in", step=0.5, dur=0.5)
    assert [float(e.get("opacity")) for e in doc.at(0.5)[3]] == pytest.approx([1, 0, 0])


def test_loops_and_errors():
    dot = svg.circle(5, 5, 5)
    dot.animate.pulse().blink().color_cycle(["red", "blue"]).shake().bounce()
    assert len(dot.children) >= 5
    with pytest.raises(TypeError, match="to_path"):
        dot.animate.morph(svg.rect(0, 0, 1, 1))


def test_show_and_hide_switch_visibility_at_their_moment():
    doc = svg.Document(20, 20)
    doc.rect(0, 0, 5, 5).animate.show(at=1)
    doc.rect(5, 0, 5, 5).animate.hide(at=1)
    assert [e.get("visibility") for e in doc.at(0.5)] == ["hidden", None]
    assert [e.get("visibility") for e in doc.at(1.5)] == ["visible", "hidden"]


def test_create_draws_the_outline_then_fills():
    doc = svg.Document(100, 100)
    doc.circle(50, 50, 20, fill="teal").animate.create(1)
    start, middle, end = (doc.at(t)[0] for t in (0, 0.3, 1))
    assert svg.Color.parse(str(start.get("stroke"))).hex == "#008080" and float(start.get("fill-opacity")) == 0
    assert 0 < float(middle.get("stroke-dashoffset")) < float(start.get("stroke-dashoffset"))
    assert float(middle.get("fill-opacity")) == 0
    assert float(end.get("stroke-dashoffset")) == 0 and float(end.get("fill-opacity")) == 1


def test_uncreate_fades_the_fill_then_draws_the_outline_off():
    doc = svg.Document(100, 100)
    doc.rect(10, 10, 40, 40, fill="red", stroke="black").animate.uncreate(1)
    start, end = doc.at(0)[0], doc.at(1)[0]
    assert float(start.get("stroke-dashoffset")) == 0 and float(start.get("fill-opacity")) == 1
    assert float(end.get("stroke-dashoffset")) == pytest.approx(160, abs=0.1) and float(end.get("fill-opacity")) == 0


def test_write_creates_text_one_character_after_another():
    doc = svg.Document(200, 60)
    doc.text("abc", x=0, y=40, font_size=30).animate.write(1)
    spans = doc.at(0.3)[0].children
    offsets = [float(span.get("stroke-dashoffset")) for span in spans]
    assert offsets[0] < offsets[1] < offsets[2]
    assert all(float(span.get("fill-opacity")) == 1 for span in doc.at(1)[0].children)
    row = svg.group(*[svg.rect(i * 10, 0, 5, 5) for i in range(3)])
    row.animate.write(1)
    begins = [float(child.children[0].get("begin").rstrip("s")) for child in row]
    assert begins[0] == 0 < begins[1] < begins[2]


def test_create_then_uncreate_chain():
    doc = svg.Document(100, 100)
    doc.circle(50, 50, 30, fill="teal").animate.create(1, begin=0.5).uncreate(1, begin=3)
    states = [(float(e.get("stroke-dashoffset")), float(e.get("fill-opacity"))) for e in (doc.at(t)[0] for t in (0, 2, 4.5))]
    assert states == [(pytest.approx(188.5, abs=0.1), 0), (0, 1), (pytest.approx(188.5, abs=0.1), 0)]

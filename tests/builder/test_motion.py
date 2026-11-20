import pytest

import svgwriter as svg
from svgwriter.builder import star


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

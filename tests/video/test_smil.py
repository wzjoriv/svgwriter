import pytest

import svgwriter as svg
from svgwriter.video._smil import clock


def _ball():
    doc = svg.Document(100, 40)
    ball = doc.circle(10, 20, 5, fill="red")
    return doc, ball


def test_clock_values():
    assert clock("2s") == 2 and clock("150ms") == 0.15 and clock("1:30") == 90 and clock("0:01:30.5") == 90.5
    assert clock("click") is None


def test_animate_interpolates_and_freezes_or_removes():
    doc, ball = _ball()
    ball.append(svg.Animate(attribute_name="cx", from_=10, to=90, dur=2, begin=1))
    assert doc.at(0.5)[0].get("cx") == 10
    assert float(doc.at(2.0)[0].get("cx")) == pytest.approx(50)
    assert doc.at(5.0)[0].get("cx") == 10
    ball.children[0].set("fill", "freeze")
    assert float(doc.at(5.0)[0].get("cx")) == pytest.approx(90)
    assert doc[0].children[0].tag == "animate" and not doc.at(1.5)[0].children


def test_values_keytimes_discrete_and_repeat():
    doc, ball = _ball()
    ball.append(svg.Animate(attribute_name="r", values="5;15;5", key_times="0;0.25;1", dur=4, repeat_count=2))
    assert float(doc.at(1.0)[0].get("r")) == pytest.approx(15)
    assert float(doc.at(5.0)[0].get("r")) == pytest.approx(15)
    doc2, ball2 = _ball()
    ball2.append(svg.Animate(attribute_name="r", values="1;2;3", calc_mode="discrete", dur=3))
    assert float(doc2.at(1.5)[0].get("r")) == 2


def test_colors_set_transform_and_motion():
    doc, ball = _ball()
    ball.append(svg.Animate(attribute_name="fill", from_="red", to="blue", dur=2))
    ball.append(svg.Set(attribute_name="stroke", to="black", begin=1))
    ball.append(svg.AnimateTransform(type="rotate", from_="0 50 20", to="90 50 20", dur=2))
    frame = doc.at(1.0)[0]
    assert frame.get("fill") == "#800080" and frame.get("stroke") == "black"
    assert frame.t.decompose()[2] == pytest.approx(45)
    doc2, ball2 = _ball()
    ball2.append(svg.AnimateMotion(path="M0 0 L80 0", dur=4))
    assert doc2.at(2.0)[0].t.apply(0, 0).x == pytest.approx(40)


def test_rendered_frames_play_smil_without_update():
    doc, ball = _ball()
    ball.append(svg.Animate(attribute_name="cx", from_=10, to=90, dur=2, fill="freeze"))
    from svgwriter.ops import render_frame

    first, last = render_frame(doc, 0.0), render_frame(doc, 2.0)
    assert first[20, 10, 1] < 128 and last[20, 90, 1] < 128 and last[20, 10, 1] > 200

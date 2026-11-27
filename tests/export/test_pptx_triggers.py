import re
import zipfile

import pytest

import svgwriter as svg

pytest.importorskip("pptx")


def _deck(tmp_path, event="click"):
    doc = svg.Document(width=400, height=300)
    key = doc.rect(20, 20, 80, 40, fill="teal")
    lamp = doc.circle(250, 100, 30, fill="gold")
    lamp.animate.on(event, key).spin(1, repeat=1, begin=0.5)
    doc.circle(300, 200, 10, fill="red").animate.fade_in(1)
    path = tmp_path / "deck.pptx"
    doc.save(path)
    return path


def test_click_starts_become_a_trigger_on_the_clicked_shape(tmp_path):
    xml = zipfile.ZipFile(_deck(tmp_path)).read("ppt/slides/slide1.xml").decode()
    assert "mainSeq" in xml and xml.count('nodeType="interactiveSeq"') == 1
    sequence = xml[xml.index("interactiveSeq"):]
    assert '<p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="2"/>' in sequence
    assert 'nodeType="clickEffect"' in sequence and '<p:cond delay="500"/>' in sequence


def test_triggers_read_back_as_click_starts(tmp_path):
    back = svg.Document.open(_deck(tmp_path)).to_string()
    begins = re.findall(r'begin="([^"]+)"', back)
    clicked = [begin for begin in begins if ".click" in begin]
    assert clicked and all(begin.endswith(".click+0.5s") for begin in clicked)
    assert f'id="{clicked[0].split(".")[0]}"' in back


def test_hover_starts_have_no_trigger_and_keep_the_resting_state(tmp_path):
    with pytest.warns(UserWarning, match="PowerPoint cannot play these animations"):
        path = _deck(tmp_path, "hover")
    xml = zipfile.ZipFile(path).read("ppt/slides/slide1.xml").decode()
    assert "interactiveSeq" not in xml

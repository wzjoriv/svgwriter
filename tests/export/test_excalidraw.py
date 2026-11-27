from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import svgwriter as svg

SAMPLE = Path(__file__).parent / "data" / "sample.excalidraw"


def scene() -> svg.Document:
    return svg.Document.open(SAMPLE)


class TestImport:
    def test_elements_map_to_native_svg(self) -> None:
        doc = scene()
        assert [e.tag for e in doc] == ["rect", "g", "g", "path", "g", "image"]
        rect = doc[0]
        assert rect.get("rx") == 15 and str(rect.get("fill")) == "#a5d8ff"

    def test_groups_dashes_rotation(self) -> None:
        group = scene()[1]
        ellipse, diamond = list(group)
        assert group.id == "group-g1" and ellipse.get("stroke-dasharray") == "8 10"
        assert diamond.tag == "polygon" and not diamond.matrix.is_identity

    def test_arrow_text_and_image(self) -> None:
        doc = scene()
        arrow = doc[2]
        assert len(arrow) == 2 and str(arrow[0].get("stroke")) == "#e03131"
        text = doc[4]
        assert [t.characters for t in text] == ["Hello", "Excalidraw"] and "Virgil" in str(text[0].get("font-family"))
        image = doc[5]
        assert image.shape == (4, 4) and image.get("opacity") == 0.6
        assert np.allclose(image.color[0, 0], (1, 0.5, 0), atol=0.01)

    def test_deleted_skipped_and_bad_input(self) -> None:
        assert all(e.get("width") != 5 for e in scene())
        with pytest.raises(ValueError, match="not an Excalidraw scene"):
            svg.formats.reader(".excalidraw").read(b'{"type": "other"}')

    def test_renders(self) -> None:
        assert scene().rasterize(background="white")[..., :3].min() < 0.2


class TestExport:
    def test_round_trip_through_excalidraw(self, tmp_path) -> None:
        doc = svg.Document(100, 50)
        doc.rect(10, 10, 30, 20, fill="#ff0000", stroke="#000000")
        doc.circle(70, 25, 15, fill="none", stroke="#0000ff", stroke_dasharray="4 2")
        doc.save(tmp_path / "x.excalidraw")
        data = json.loads((tmp_path / "x.excalidraw").read_text())
        assert data["type"] == "excalidraw" and len(data["elements"]) == 2
        rect, circle = data["elements"]
        assert rect["backgroundColor"] == "#ff0000" and circle["strokeStyle"] == "dashed"
        back = svg.Document.open(tmp_path / "x.excalidraw")
        assert back[0].exact_bbox() == pytest.approx((10, 10, 30, 20), abs=0.01)


def test_transparent_stroke_reads_as_none():
    import json

    from svgwriter.formats.export._scene._excalidraw import read_excalidraw

    scene = {"type": "excalidraw", "elements": [{"type": "rectangle", "x": 0, "y": 0, "width": 4, "height": 4,
                                                 "strokeColor": "transparent", "backgroundColor": "#ff0000"}]}
    rect = read_excalidraw(json.dumps(scene))[0]
    assert rect.get("stroke") == "none" and rect.get("fill") == "#ff0000"

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.formats.inkscape import Arc, Guide, Star

DATA = Path(__file__).parent / "data"
INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"


@pytest.fixture
def doc() -> svg.Document:
    return svg.Document.open(DATA / "drawing.svg")


class TestNamespaces:
    def test_prefixes_kept_and_declared_once(self, doc: svg.Document) -> None:
        text = doc.to_string()
        assert "ns0" not in text
        assert text.count('xmlns:inkscape="') == 1 and text.count('xmlns:sodipodi="') == 1
        assert "<sodipodi:namedview" in text and "<inkscape:path-effect" in text and "<dc:title>" in text
        root = ET.fromstring(text)
        assert root.find(f"{{{SODIPODI}}}namedview") is not None

    def test_round_trip_is_stable(self, doc: svg.Document) -> None:
        first = doc.to_string()
        assert svg.Document.from_string(first).to_string() == first

    def test_new_document_declares_used_prefixes(self) -> None:
        doc = svg.Document(10, 10)
        doc.rect(0, 0, 1, 1, inkscape_label="a")
        text = doc.to_string()
        assert f'xmlns:inkscape="{INKSCAPE}"' in text and "sodipodi" not in text

    def test_unknown_prefix_kept(self) -> None:
        source = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:serif="http://www.serif.com/"><g serif:id="A"/></svg>'
        text = svg.parse(source).to_string(xml_declaration=False, pretty=False)
        assert 'xmlns:serif="http://www.serif.com/"' in text and 'serif:id="A"' in text

    def test_path_effect_untouched(self, doc: svg.Document) -> None:
        curve = doc["curve"]
        assert curve.get("inkscape:path-effect") == "#path-effect1"
        assert curve.get("inkscape:original-d") == "M 10,90 C 40,80 60,95 90,90"


class TestLayersAndLabels:
    def test_layers_by_label(self, doc: svg.Document) -> None:
        assert list(doc.layers) == ["Background", "Shapes"]
        assert doc.layers["Shapes"].id == "layer2"

    def test_layer_finds_or_adds(self, doc: svg.Document) -> None:
        assert doc.layer("Shapes") is doc.layers["Shapes"]
        with doc.layer("Notes") as notes:
            doc.rect(0, 0, 1, 1)
            sub = doc.layer("Inner")
        assert sub.parent is notes and list(doc.layers)[-2:] == ["Notes", "Inner"]
        assert 'inkscape:groupmode="layer"' in doc.to_string()

    def test_label_lookup(self, doc: svg.Document) -> None:
        assert doc["Logo"] is doc["star"] and doc["Logo"].label == "Logo"
        assert "Paper" in doc and "nothing" not in doc
        with pytest.raises(KeyError):
            doc["nothing"]

    def test_duplicate_label_is_ambiguous(self) -> None:
        doc = svg.Document(10, 10)
        doc.rect(0, 0, 1, 1, inkscape_label="twin")
        doc.rect(2, 0, 1, 1, inkscape_label="twin")
        with pytest.raises(KeyError, match="2 elements"):
            doc["twin"]

    def test_id_wins_over_label(self) -> None:
        doc = svg.Document(10, 10)
        first = doc.rect(0, 0, 1, 1, id="a")
        doc.rect(2, 0, 1, 1, inkscape_label="a")
        assert doc["a"] is first

    def test_namedview_is_not_content(self, doc: svg.Document) -> None:
        assert [element.tag for element in doc] == ["g", "g"]


class TestTransformCenter:
    def test_read_into_anchor(self, doc: svg.Document) -> None:
        box = doc["box"]
        assert box.anchor == svg.Point(110.0, 20.0)
        assert "inkscape:transform-center-x" not in box.attributes

    def test_written_back(self, doc: svg.Document) -> None:
        text = doc.to_string()
        assert 'inkscape:transform-center-x="10"' in text and 'inkscape:transform-center-y="5"' in text

    def test_follows_rotation(self, doc: svg.Document) -> None:
        doc["box"].rotate(90)
        root = ET.fromstring(doc.to_string())
        box = next(e for e in root.iter() if e.get("id") == "box")
        assert float(box.get(f"{{{INKSCAPE}}}transform-center-x")) == pytest.approx(5)
        assert float(box.get(f"{{{INKSCAPE}}}transform-center-y")) == pytest.approx(-10)

    def test_only_in_inkscape_documents(self) -> None:
        doc = svg.Document(10, 10)
        doc.rect(0, 0, 4, 4, anchor=(0, 0))
        assert "transform-center" not in doc.to_string()


class TestShapes:
    def test_star_parameters(self, doc: svg.Document) -> None:
        star = svg.inkscape.shape(doc["star"])
        assert isinstance(star, Star)
        assert (star.sides, star.outer, star.inner, star.flatsided) == (5, 20, 10, False)
        assert star.angle == pytest.approx(-90)
        assert star.skew == pytest.approx(0, abs=1e-5)

    def test_star_edit_redraws(self, doc: svg.Document) -> None:
        star = Star(doc["star"])
        star.sides = 7
        assert doc["star"].get("sodipodi:sides") == 7
        assert len(doc["star"].d) == 2 * 7 + 1
        assert doc["star"].bbox.height == pytest.approx(20 + 20 * max(math.sin(math.radians(360 / 7 * k - 90)) for k in range(7)))

    def test_rounded_matches_inkscape(self) -> None:
        path = Star.create(150, 70, 20, 10, 5, rounded=0.3)
        first = path.d[1]
        assert (first.x1, first.y1) == pytest.approx((153.98439, 50), abs=1e-4)

    def test_polygon(self) -> None:
        hexagon = svg.paths.regular_polygon(0, 0, 10, 6, inkscape=True)
        assert Star(hexagon).flatsided and hexagon.bbox.height == pytest.approx(20)

    def test_builder_star(self) -> None:
        drawn = svg.paths.star(50, 50, 40, inkscape=True, fill="gold")
        plain = svg.paths.star(50, 50, 40)
        assert drawn.bbox.width == pytest.approx(plain.bbox.width)
        with pytest.raises(ValueError, match="corner_radius"):
            svg.paths.star(0, 0, 4, inkscape=True, corner_radius=1)

    def test_arc(self, doc: svg.Document) -> None:
        pie = Arc(doc["pie"])
        assert (pie.kind, pie.start, pie.end) == ("slice", 0, pytest.approx(90))
        pie.end = 180
        assert doc["pie"].bbox.height == pytest.approx(20)
        pie.kind = "arc"
        assert str(doc["pie"].d).count("Z") == 0
        with pytest.raises(ValueError):
            pie.kind = "wedge"

    def test_not_a_shape(self) -> None:
        with pytest.raises(ValueError, match="not an Inkscape star"):
            Star(svg.Path("M0 0"))


class TestConnectors:
    def test_read(self, doc: svg.Document) -> None:
        start, end = doc["wire"].connects
        assert start is doc["pie"] and end is doc["star"]
        assert doc["curve"].connects is None

    def test_write_and_detach(self) -> None:
        doc = svg.Document(100, 40)
        a, b = doc.rect(0, 0, 10, 10), doc.rect(80, 0, 10, 10)
        wire = doc.path()
        wire.connects = (a, b)
        assert wire.get("inkscape:connection-start") == f"#{a.id}"
        assert svg.Document.from_string(doc.to_string())[2].connects.end.id == b.id
        wire.connects = None
        assert "inkscape:connector-type" not in wire.attributes


class TestGuidesAndHints:
    def test_read_guides(self, doc: svg.Document) -> None:
        margin, base = doc.guides
        assert (margin.x, margin.angle, margin.label, margin.locked) == (20, 90, "margin", False)
        assert (base.y, base.angle, base.locked) == (30, 0, True)

    def test_write_guides(self, doc: svg.Document) -> None:
        doc.guides = [Guide(10, 10, 45, color="#ff0000")]
        doc.guide(y=25)
        again = svg.Document.from_string(doc.to_string())
        assert [(g.x, g.y, round(g.angle)) for g in again.guides] == [(10, 10, 45), (0, 25, 0)]
        assert again.guides[0].color == "#ff0000"
        with pytest.raises(TypeError):
            doc.guide()

    def test_export_hints(self, doc: svg.Document) -> None:
        hints = doc.export_hints
        assert (hints.dpi, hints.filename, hints.units) == (192, "drawing.png", "mm")

    def test_png_uses_hint(self) -> None:
        doc = svg.Document(10, 10)
        doc.export_hints = svg.inkscape.ExportHints(dpi=192)
        width = int.from_bytes(doc.export("png")[16:20], "big")
        explicit = int.from_bytes(doc.export("png", scale=1)[16:20], "big")
        assert (width, explicit) == (20, 10)

from __future__ import annotations

import math

import pytest

import svgwriter as svg
from svgwriter._internal._flat._flatten import polylines
from svgwriter.formats.export._plotter._constants import MM_PER_USER_UNIT
from svgwriter.model.pathdata import PathData


def drawing() -> svg.Document:
    doc = svg.Document(96, 96)
    doc.rect(0, 0, 96, 48, fill="none", stroke="red")
    doc.circle(48, 72, 20, fill="blue")
    return doc


def test_polylines_flatten_within_tolerance() -> None:
    (points, closed), = polylines(PathData("M0 0 C0 100 100 100 100 0 Z"), 0.1)
    assert closed and points[0] == points[-1] and len(points) > 10
    coarse, = polylines(PathData("M0 0 C0 100 100 100 100 0"), 10)
    assert len(coarse[0]) < len(points)


def test_dxf_reads_back_with_ezdxf(tmp_path) -> None:
    ezdxf = pytest.importorskip("ezdxf")
    drawing().save(tmp_path / "x.dxf")
    entities = list(ezdxf.readfile(tmp_path / "x.dxf").modelspace())
    assert len(entities) == 2 and {e.dxf.layer for e in entities} == {"FF0000", "0000FF"}
    rect = next(e for e in entities if e.dxf.layer == "FF0000")
    xs = [v.dxf.location.x for v in rect.vertices]
    ys = [v.dxf.location.y for v in rect.vertices]
    assert rect.is_closed and max(xs) == pytest.approx(25.4) and min(ys) == pytest.approx(12.7)


def test_hpgl_pens_and_units() -> None:
    text = drawing().export("hpgl")
    assert text.startswith("IN;") and "SP1;PU0,1016;" in text and "SP2;" in text and text.rstrip().endswith("PU;SP0;")


def test_gcode_mill_and_laser() -> None:
    mill = drawing().export("gcode", feed=500)
    assert mill.startswith("G21") and "G1 Z-0.5 F500" in mill and "G0 Z2" in mill and mill.rstrip().endswith("M2")
    laser = drawing().export("gcode", mode="laser", power=300)
    assert "M3 S300" in laser and "M5" in laser and "Z" not in laser.replace("G21", "")
    first = next(line for line in mill.splitlines() if line.startswith("G0 X"))
    assert first == f"G0 X0 Y{48 * MM_PER_USER_UNIT * 2:.4f}".rstrip("0").rstrip(".")


def test_extension_lookup() -> None:
    assert {svg.FORMATS.writer(f"a{e}").name for e in (".dxf", ".plt", ".nc", ".gcode")} == {"dxf", "hpgl", "gcode"}


def test_matplotlib_figures_can_be_added() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(2, 1))
    ax.plot([0, 1], [0, 1])
    doc = svg.Document(400, 200)
    group = doc.add(fig).translate(10, 10)
    plt.close(fig)
    assert isinstance(group, svg.Group) and group.find(svg.Path) is not None
    assert doc.rasterize()[..., 3].max() == 1.0
    box = doc.content_bounds()
    assert box is not None and math.isfinite(box.width) and box.x == 10


class TestImport:
    @pytest.mark.parametrize("extension", [".dxf", ".plt", ".gcode"])
    def test_round_trip_keeps_geometry(self, tmp_path, extension: str) -> None:
        doc = drawing()
        path = tmp_path / f"x{extension}"
        doc.save(path)
        back = svg.Document.open(path)
        original = doc.content_bounds()
        box = back.content_bounds()
        assert len(back) == 2 and box is not None
        assert box.width == pytest.approx(original.width, abs=1.5) and box.height == pytest.approx(original.height, abs=1.5)

    def test_dxf_colours_from_layers(self, tmp_path) -> None:
        drawing().save(tmp_path / "x.dxf")
        back = svg.Document.open(tmp_path / "x.dxf")
        assert {str(p.get("stroke")) for p in back} == {"#ff0000", "#0000ff"}

    def test_ezdxf_entities(self, tmp_path) -> None:
        ezdxf = pytest.importorskip("ezdxf")
        dxf = ezdxf.new("R2010")
        msp = dxf.modelspace()
        msp.add_circle((10, 10), 5)
        msp.add_arc((30, 10), 5, 0, 90)
        msp.add_lwpolyline([(0, 0, 0, 0, 1.0), (10, 0)], format="xyseb")
        msp.add_line((0, 20), (40, 20))
        msp.add_ellipse((50, 10), major_axis=(5, 0), ratio=0.5)
        dxf.saveas(tmp_path / "e.dxf")
        back = svg.Document.open(tmp_path / "e.dxf", unit_mm=1.0)
        assert len(back) == 5
        circle = back[0].exact_bbox()
        assert circle.width == pytest.approx(10, abs=0.05)
        bulge = back[2].exact_bbox()
        assert bulge.height == pytest.approx(5, abs=0.1)

    def test_gcode_arcs_inches_and_laser(self) -> None:
        from svgwriter.formats.export._plotter._cnc_read import read_gcode

        doc = read_gcode("G20\nM3\nG0 X0 Y0\nG1 X1 Y0\nG2 X1 Y-2 I0 J-1\nM5\nG0 X5 Y5\n", unit_mm=1.0)
        (path,) = list(doc)
        box = path.exact_bbox()
        assert box.width == pytest.approx(25.4 * 2, abs=0.5) and box.height == pytest.approx(50.8, abs=0.5)

    def test_hpgl_relative_and_pens(self) -> None:
        from svgwriter.formats.export._plotter._cnc_read import read_hpgl

        doc = read_hpgl("IN;SP2;PU0,0;PD400,0;PR0,400;PU;SP5;PA0,0;PD0,800;", unit_mm=1.0)
        assert [str(p.get("stroke")) for p in doc] == ["red", "blue"]
        assert doc[0].exact_bbox() == pytest.approx((0, 10, 10, 10))


@pytest.mark.parametrize("fmt", ["dxf", "gcode"])
def test_round_trip_keeps_position_and_page(fmt):
    import svgwriter as svg

    doc = svg.Document(100, 50)
    doc.rect(10, 5, 20, 10, stroke="black", fill="none")
    back = svg.FORMATS.reader(fmt).read(svg.export.export(doc, fmt).encode())
    box = back[0].bounds()
    assert (box.x, box.y, box.width, box.height) == pytest.approx((10, 5, 20, 10), abs=1e-3)
    assert (back.root.view_box.width, back.root.view_box.height) == pytest.approx((100, 50), abs=1e-3)


def test_hpgl_without_page_flips_about_drawing_top():
    import svgwriter as svg

    doc = svg.Document(100, 50)
    doc.rect(10, 5, 20, 10, stroke="black", fill="none")
    back = svg.FORMATS.reader("hpgl").read(svg.export.export(doc, "hpgl").encode())
    assert back[0].bounds().y == pytest.approx(0, abs=1e-3)

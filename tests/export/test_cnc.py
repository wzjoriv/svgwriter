from __future__ import annotations

import math

import pytest

import svgwriter as svg
from svgwriter.export._cnc import MM_PER_USER_UNIT, polylines
from svgwriter.path import PathData


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
    assert {svg.export.find_exporter(f"a{e}").name for e in (".dxf", ".plt", ".nc", ".gcode")} == {"dxf", "hpgl", "gcode"}


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

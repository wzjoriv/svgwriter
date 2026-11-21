import shutil
import sys
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.errors import DiagramToolError
from svgwriter.formats.export._diagram import read_dot, read_mermaid

SVG_OUT = b'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10"><rect width="20" height="10"/></svg>'


def _fake_tool(tmp_path: Path, name: str, body: str) -> str:
    script = tmp_path / f"{name}.py"
    script.write_text(body, encoding="utf-8")
    launcher = tmp_path / (f"{name}.bat" if sys.platform == "win32" else name)
    if sys.platform == "win32":
        launcher.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
    else:
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
    return str(launcher)


def test_missing_tool_names_the_install(monkeypatch):
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("SVGWRITER_DOT", raising=False)
    with pytest.raises(DiagramToolError, match="Graphviz"):
        read_dot(b"digraph { a -> b }")


def test_dot_output_becomes_a_document(monkeypatch, tmp_path):
    tool = _fake_tool(tmp_path, "dot", f"import sys; sys.stdin.read(); sys.stdout.buffer.write({SVG_OUT!r})")
    monkeypatch.setenv("SVGWRITER_DOT", tool)
    doc = read_dot(b"digraph { a -> b }")
    assert [e.tag for e in doc] == ["rect"]


def test_tool_errors_are_reported(monkeypatch, tmp_path):
    tool = _fake_tool(tmp_path, "dot", "import sys; sys.stderr.write('syntax error in line 1'); sys.exit(1)")
    monkeypatch.setenv("SVGWRITER_DOT", tool)
    with pytest.raises(DiagramToolError, match="syntax error"):
        read_dot(b"digraph {")


def test_mermaid_runs_with_svg_labels(monkeypatch, tmp_path):
    body = (
        "import sys, json, pathlib\n"
        "args = sys.argv[1:]\n"
        "config = json.loads(pathlib.Path(args[args.index('-c') + 1]).read_text())\n"
        "assert config['flowchart']['htmlLabels'] is False\n"
        f"pathlib.Path(args[args.index('-o') + 1]).write_bytes({SVG_OUT!r})\n"
    )
    monkeypatch.setenv("SVGWRITER_MMDC", _fake_tool(tmp_path, "mmdc", body))
    assert len(read_mermaid(b"graph TD; A-->B")) == 1


def test_extensions_route_to_the_importers():
    assert svg.formats.reader("x.gv").name == "dot"
    assert svg.formats.reader("x.mmd").name == "mermaid"


@pytest.mark.skipif(shutil.which("latex") is None or shutil.which("dvisvgm") is None, reason="no TeX installed")
def test_latex_formula_becomes_outlines():
    formula = svg.latex(r"\frac{a}{b}", display=True)
    box = formula.bounds()
    assert formula.tag == "g" and box is not None and box.height > box.width * 0.5


def test_latex_falls_back_to_mathtext_without_tex(monkeypatch):
    pytest.importorskip("matplotlib")
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("SVGWRITER_LATEX", raising=False)
    formula = svg.latex(r"\frac{a}{b}")
    assert formula.tag == "g" and formula.bounds() is not None


def test_latex_reports_missing_tools_without_any_fallback(monkeypatch):
    import sys

    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("SVGWRITER_LATEX", raising=False)
    for name in ("matplotlib", "matplotlib.font_manager", "matplotlib.textpath", "ziamath"):
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(DiagramToolError, match="TeX"):
        svg.latex("x")


def test_plantuml_and_d2_use_their_tools(monkeypatch, tmp_path):
    from svgwriter.formats.export._diagram import read_d2, read_plantuml

    monkeypatch.setenv("SVGWRITER_PLANTUML", _fake_tool(
        tmp_path, "plantuml", f"import sys; sys.stdin.read(); sys.stdout.buffer.write({SVG_OUT!r})"))
    assert len(read_plantuml(b"@startuml\nA -> B\n@enduml")) == 1
    body = f"import sys, pathlib; pathlib.Path(sys.argv[2]).write_bytes({SVG_OUT!r})"
    monkeypatch.setenv("SVGWRITER_D2", _fake_tool(tmp_path, "d2", body))
    assert len(read_d2(b"a -> b")) == 1


@pytest.mark.parametrize("engine", ["ziamath", "mathtext"])
def test_python_math_engines(engine):
    pytest.importorskip("ziamath" if engine == "ziamath" else "matplotlib")
    formula = svg.latex(r"\frac{a}{b}", display=True, engine=engine)
    box = formula.bounds()
    assert formula.tag == "g" and box is not None and box.height > box.width * 0.5


def test_unknown_engine():
    with pytest.raises(ValueError, match="engine"):
        svg.latex("x", engine="mathjax")


def test_svg2_href_and_symbols_resolve():
    markup = ('<svg xmlns="http://www.w3.org/2000/svg"><symbol id="s" viewBox="0 0 10 10">'
              '<rect width="10" height="10"/></symbol><use href="#s" x="5" width="20" height="20"/></svg>')
    use = next(svg.parse(markup).iter("use"))
    assert use.get("xlink:href") is not None and use.to_path().bounds() == pytest.approx((5, 0, 20, 20))


class TestMermaidFlowcharts:
    SOURCE = """flowchart TD
      A[Start] -->|go| B{Choice} & C((Circle))
      B -.-> D[(Store)]
      C ==> D
      D --> A
      subgraph Group
        B
        C
      end
    """

    def test_parse_shapes_edges_and_subgraphs(self):
        from svgwriter.formats.export._diagram._mermaid import parse_flowchart

        chart = parse_flowchart(self.SOURCE)
        assert [(n.id, n.shape) for n in chart.nodes.values()] == [
            ("A", "rect"), ("B", "diamond"), ("C", "circle"), ("D", "cylinder")]
        assert [(e.source, e.target, e.label, e.style) for e in chart.edges] == [
            ("A", "B", "go", "solid"), ("A", "C", "go", "solid"), ("B", "D", "", "dotted"),
            ("C", "D", "", "thick"), ("D", "A", "", "solid")]
        assert chart.subgraphs == [("Group", ["B", "C"])]

    def test_layout_ranks_top_to_bottom_and_left_to_right(self):
        from svgwriter.formats.export._diagram._mermaid import draw_flowchart, parse_flowchart

        chart = parse_flowchart(self.SOURCE)
        draw_flowchart(chart)
        assert chart.nodes["A"].y < chart.nodes["B"].y < chart.nodes["D"].y
        sideways = parse_flowchart("graph LR\n  A --> B")
        draw_flowchart(sideways)
        assert sideways.nodes["A"].x < sideways.nodes["B"].x

    def test_read_mermaid_uses_the_builtin_layout_without_mmdc(self, monkeypatch):
        monkeypatch.setenv("PATH", "")
        monkeypatch.delenv("SVGWRITER_MMDC", raising=False)
        doc = read_mermaid(self.SOURCE.encode())
        assert len(list(doc.root.iter("text"))) >= 4
        with pytest.raises(DiagramToolError, match="mmdc"):
            read_mermaid(b"sequenceDiagram\n  A->>B: hi")

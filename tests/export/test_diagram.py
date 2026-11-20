import shutil
import sys
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.export._diagram import DiagramToolError, read_dot, read_mermaid

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
    assert svg.export.find_importer("x.gv").name == "dot"
    assert svg.export.find_importer("x.mmd").name == "mermaid"


@pytest.mark.skipif(shutil.which("latex") is None or shutil.which("dvisvgm") is None, reason="no TeX installed")
def test_latex_formula_becomes_outlines():
    formula = svg.latex(r"\frac{a}{b}", display=True)
    box = formula.bounds()
    assert formula.tag == "g" and box is not None and box.height > box.width * 0.5


def test_latex_reports_missing_tools(monkeypatch):
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("SVGWRITER_LATEX", raising=False)
    with pytest.raises(DiagramToolError, match="TeX"):
        svg.latex("x")


def test_plantuml_and_d2_use_their_tools(monkeypatch, tmp_path):
    from svgwriter.export._diagram import read_d2, read_plantuml

    monkeypatch.setenv("SVGWRITER_PLANTUML", _fake_tool(
        tmp_path, "plantuml", f"import sys; sys.stdin.read(); sys.stdout.buffer.write({SVG_OUT!r})"))
    assert len(read_plantuml(b"@startuml\nA -> B\n@enduml")) == 1
    body = f"import sys, pathlib; pathlib.Path(sys.argv[2]).write_bytes({SVG_OUT!r})"
    monkeypatch.setenv("SVGWRITER_D2", _fake_tool(tmp_path, "d2", body))
    assert len(read_d2(b"a -> b")) == 1

from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "inkscape"
DRAWING = Path(__file__).parent / "data" / "drawing.svg"
SVG = "{http://www.w3.org/2000/svg}"


def run(script: str, *arguments: str, drawing: Path = DRAWING) -> subprocess.CompletedProcess[bytes]:
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("SVGWRITER_PYTHON", None)
    return subprocess.run([sys.executable, str(PLUGIN / script), *arguments, str(drawing)], capture_output=True,
                          env=env, check=False, timeout=120)


def element(output: bytes, element_id: str) -> ET.Element:
    root = ET.fromstring(output)
    return next(node for node in root.iter() if node.get("id") == element_id)


def test_inx_files_are_wellformed() -> None:
    names = sorted(path.name for path in PLUGIN.glob("*.inx"))
    assert names == ["svgwriter_export.inx", "svgwriter_script.inx", "svgwriter_theme.inx"]
    for path in PLUGIN.glob("*.inx"):
        root = ET.parse(path).getroot()
        command = root.find(".//{http://www.inkscape.org/namespace/inkscape/extension}command")
        assert command is not None and (PLUGIN / command.text).is_file()


class TestScript:
    def test_code_edits_the_drawing(self) -> None:
        code = 'doc["Logo"].rotate(30)\\nfor item in selection:\\n    item.label = "picked"'
        result = run("svgwriter_script.py", f"--code={code}", "--id=box")
        assert result.returncode == 0, result.stderr
        assert element(result.stdout, "star").get("transform", "").startswith("rotate(30")
        assert element(result.stdout, "box").get("{http://www.inkscape.org/namespaces/inkscape}label") == "picked"
        assert b"ns0:" not in result.stdout

    def test_ordinary_scripts_and_animation(self, tmp_path: Path) -> None:
        script = tmp_path / "title.py"
        script.write_text(
            'doc.text("Hello", x=20, y=20, id="title", font_size=8)\n'
            'doc["title"].animate.typewriter(dur=2)\n'
            "def ring(count):\n"
            "    for k in range(count):\n"
            "        doc.circle(100 + 30 * math.cos(k), 50 + 30 * math.sin(k), 2)\n"
            "ring(4)\n", encoding="utf-8")
        result = run("svgwriter_script.py", f"--script={script}")
        assert result.returncode == 0, result.stderr
        root = ET.fromstring(result.stdout)
        assert root.find(f".//{SVG}set") is not None
        assert len(root.findall(f".//{SVG}circle")) == 4

    def test_missing_font_family_warns(self) -> None:
        code = 'label = doc.text("Hi", x=0, y=10, font_family="Zz No Such Family")\\nassert label.bounds() is not None'
        result = run("svgwriter_script.py", f"--code={code}")
        assert result.returncode == 0, result.stderr
        assert b"Zz No Such Family" in result.stdout
        assert b"Warning:" in result.stderr and b"not found" in result.stderr

    def test_error_reports_line(self) -> None:
        result = run("svgwriter_script.py", '--code=x = 1\\ndoc["nothing"]')
        assert result.returncode == 1
        assert b"Line 2" in result.stderr and b"KeyError" in result.stderr

    def test_syntax_error_reports_line(self) -> None:
        result = run("svgwriter_script.py", "--code=x = (")
        assert result.returncode == 1 and b"Line 1" in result.stderr


class TestExport:
    @pytest.mark.parametrize("extension", ["tikz", "gcode"])
    def test_formats(self, tmp_path: Path, extension: str) -> None:
        target = tmp_path / f"out.{extension}"
        result = run("svgwriter_export.py", f"--output={target}")
        assert result.returncode == 0, result.stderr
        assert target.stat().st_size > 0 and ET.fromstring(result.stdout) is not None

    def test_options_and_format(self, tmp_path: Path) -> None:
        target = tmp_path / "picture.bin"
        result = run("svgwriter_export.py", f"--output={target}", "--format=png", "--options=dpi=48")
        assert result.returncode == 0, result.stderr
        assert int.from_bytes(target.read_bytes()[16:20], "big") == 378

    def test_unknown_extension(self, tmp_path: Path) -> None:
        result = run("svgwriter_export.py", f"--output={tmp_path / 'a.xyz'}")
        assert result.returncode == 1 and b"could not save" in result.stderr


class TestTheme:
    def test_role_and_theme(self) -> None:
        result = run("svgwriter_theme.py", "--theme=dark", "--role=accent", "--id=box")
        assert result.returncode == 0, result.stderr
        assert element(result.stdout, "box").get("class") == "role-accent"
        assert b".role-accent" in result.stdout

    def test_unknown_role(self) -> None:
        result = run("svgwriter_theme.py", "--role=nope", "--id=box")
        assert result.returncode == 1 and b"no role 'nope'" in result.stderr

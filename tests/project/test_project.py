from __future__ import annotations

import importlib.util
import json
import struct
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter._internal._typography._fonts import registered_typefaces
from svgwriter.tools.project import ProjectError

from ..conftest import wellformed

PNG_SIZE = slice(16, 24)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG")
    return struct.unpack(">II", data[PNG_SIZE])


def check_output(path: Path) -> None:
    """The file exists and is a valid file of its kind."""
    assert path.is_file() and path.stat().st_size > 0, path
    suffix = path.suffix
    if suffix == ".svg":
        wellformed(path.read_text(encoding="utf-8"))
    elif suffix == ".png":
        assert min(png_size(path)) > 0
    elif suffix == ".pdf":
        assert path.read_bytes().startswith(b"%PDF") and svg.Document.open_all(path)
    elif suffix == ".gif":
        assert path.read_bytes()[:6] == b"GIF89a"
    elif suffix == ".pptx":
        pptx = pytest.importorskip("pptx")
        assert len(pptx.Presentation(str(path)).slides) > 0


class TestPresets:
    @pytest.mark.parametrize(("preset", "names"), [
        ("blank", ["demo.svg", "demo.png"]),
        ("poster", ["demo.pdf", "demo.svg", "demo.png"]),
        ("slides", ["demo.pptx", "demo.pdf"]),
        ("animation", ["demo.gif", "demo.svg"]),
    ])
    def test_create_and_build(self, tmp_path: Path, preset: str, names: list[str]) -> None:
        if preset == "slides":
            pytest.importorskip("pptx")
        project = svg.Project.new(tmp_path / "demo", preset=preset)
        layout = {"svgwriter.toml", "main.py", "theme.toml", "README.md", ".gitignore", "components/__init__.py",
                  "components/title_block.py", "animations/__init__.py", "animations/bob.py",
                  "assets/fonts/.gitkeep", "assets/images/.gitkeep", "assets/data/.gitkeep"}
        files = {path.relative_to(project.root).as_posix() for path in project.root.rglob("*") if path.is_file()}
        assert layout <= files and not any(name.endswith("-tpl") for name in files)
        written = project.build()
        assert [path.name for path in written] == names
        for path in written:
            check_output(path)
        assert "bob" not in svg.preset.animation.list()

    def test_poster_is_a4_in_millimetres(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "sheet", preset="poster")
        svg_file, png_file = project.build(["svg", "png"])
        root = svg.Document.open(svg_file).root
        assert str(root.get("width")) == "210mm" and root.view_box.width == 210
        assert png_size(png_file) == (1241, 1755)

    def test_slides_make_one_slide_each(self, tmp_path: Path) -> None:
        pptx = pytest.importorskip("pptx")
        deck = svg.Project.new(tmp_path / "talk", preset="slides").build()
        presentation = pptx.Presentation(str(deck[0]))
        assert len(presentation.slides) == 3 and presentation.slide_width == 12192000
        assert len(svg.Document.open_all(deck[1])) == 3

    def test_theme_file_is_applied(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "themed")
        (project.root / "theme.toml").write_text('extends = "dark"\n[palette]\nprimary = "#123456"\n', encoding="utf-8")
        text = project.build(["svg"])[0].read_text(encoding="utf-8")
        assert "#123456" in text.lower()

    def test_theme_applies_to_scenes_made_on_import(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "swept")
        (project.root / "theme.toml").write_text('extends = "dark"\n[roles.felt]\nfill = "#123456"\n', encoding="utf-8")
        (project.root / "main.py").write_text(
            "import svgwriter as svg\n"
            "def page(doc, size=10):\n    doc.rect(0, 0, size, size).as_role('felt')\n"
            "sweep = svg.sweep(page, size=(10, 20), dur=0.5, fps=4)\n"
            "build = [page, sweep]\n", encoding="utf-8")
        written = project.build(["svg"])
        assert all("#123456" in path.read_text(encoding="utf-8").lower() for path in written)

    def test_fonts_are_registered(self, tmp_path: Path) -> None:
        from ..ops.test_fonts import _box_font

        project = svg.Project.new(tmp_path / "typed")
        (project.root / "assets" / "fonts" / "box.ttf").write_bytes(_box_font("ProjectBoxTest"))
        project.build(["svg"])
        assert "projectboxtest" in registered_typefaces

    def test_rebuild_sees_edits(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "edit")
        first = project.build(["svg"])[0].read_text(encoding="utf-8")
        main = project.root / "main.py"
        main.write_text(main.read_text(encoding="utf-8").replace("Edit main.py", "Changed text"), encoding="utf-8")
        second = project.build(["svg"])[0].read_text(encoding="utf-8")
        assert "Changed text" not in first and "Changed text" in second

    def test_register_preset_extends(self, tmp_path: Path) -> None:
        folder = tmp_path / "badge-preset"
        folder.mkdir()
        (folder / "svgwriter.toml").write_text('[project]\nname = "{{ project_name }}"\nsize = "icon"\n'
                                               '[outputs]\nformats = ["svg"]\n', encoding="utf-8")
        svg.project.PRESETS.register(svg.project.Preset("badge", "A square icon", folder, extends="blank"))
        try:
            assert "badge" in svg.project.PRESETS.list()
            project = svg.Project.new(tmp_path / "logo", preset="badge")
            assert (project.root / "components" / "title_block.py").is_file()
            assert [path.name for path in project.build()] == ["logo.svg"]
        finally:
            svg.project.PRESETS.unregister("badge")


class TestConfig:
    def test_svgwriter_toml_wins_over_pyproject(self, tmp_path: Path) -> None:
        (tmp_path / "svgwriter.toml").write_text('[project]\nname = "own"\n', encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text('[tool.svgwriter.project]\nname = "table"\n', encoding="utf-8")
        assert svg.Project.load(tmp_path).name == "own"

    def test_pyproject_table(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "pkg"\n[tool.svgwriter.project]\nname = "table"\n'
                                                 'size = "letter"\n[tool.svgwriter.outputs]\nformats = ["pdf"]\n',
                                                 encoding="utf-8")
        nested = tmp_path / "nested"
        nested.mkdir()
        project = svg.Project.load(nested)
        assert project.name == "table" and project.config.size == "letter" and project.config.formats == ("pdf",)
        assert project.root == tmp_path.resolve()

    def test_pyproject_without_table_is_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "svgwriter.toml").write_text('[project]\nname = "outer"\n', encoding="utf-8")
        inner = tmp_path / "inner"
        inner.mkdir()
        (inner / "pyproject.toml").write_text('[project]\nname = "pkg"\n', encoding="utf-8")
        assert svg.Project.load(inner).name == "outer"

    def test_no_manifest(self, tmp_path: Path) -> None:
        with pytest.raises(ProjectError, match="svgwriter new"):
            svg.Project.load(tmp_path)

    @pytest.mark.parametrize(("text", "message"), [
        ('[project]\nentyr = "main:build"\n', r"unknown key project\.'entyr'"),
        ('[outputs]\nformats = ["svg", "nope"]\n', "unknown format 'nope'"),
        ('[outputs]\npng = 2\n', r"outputs\.png is a table"),
        ('[project]\nsize = "a44"\n', "did you mean 'a4'"),
        ('[project]\nsize = 3\n', "project.size is a size name"),
        ('[colours]\n', "unknown key 'colours'"),
        ('[project\n', "svgwriter.toml"),
    ])
    def test_bad_manifest_names_file_and_key(self, tmp_path: Path, text: str, message: str) -> None:
        (tmp_path / "svgwriter.toml").write_text(text, encoding="utf-8")
        with pytest.raises(ProjectError, match=message) as raised:
            svg.Project.load(tmp_path)
        assert "svgwriter.toml" in str(raised.value)


class TestErrors:
    def test_unknown_preset_lists_presets(self, tmp_path: Path) -> None:
        with pytest.raises(ProjectError, match="did you mean 'poster'.*blank, poster, slides, animation"):
            svg.Project.new(tmp_path / "x", preset="postr")

    def test_folder_must_be_new(self, tmp_path: Path) -> None:
        (tmp_path / "taken").mkdir()
        (tmp_path / "taken" / "file.txt").write_text("x", encoding="utf-8")
        with pytest.raises(ProjectError, match="not empty"):
            svg.Project.new(tmp_path / "taken")

    def test_missing_entry_module_and_object(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "broken")
        (project.root / "main.py").unlink()
        with pytest.raises(ProjectError, match="no module 'main'"):
            project.build()
        (project.root / "main.py").write_text("x = 1\n", encoding="utf-8")
        with pytest.raises(ProjectError, match="main.py has no 'build'"):
            project.build()

    def test_entry_of_the_wrong_kind(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "odd")
        (project.root / "main.py").write_text("build = 42\n", encoding="utf-8")
        with pytest.raises(ProjectError, match="gives int"):
            project.build()

    def test_import_errors_inside_the_project_surface(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "deps")
        (project.root / "main.py").write_text("import not_installed_module_xyz\n", encoding="utf-8")
        with pytest.raises(ModuleNotFoundError, match="not_installed_module_xyz"):
            project.build()

    def test_missing_theme_file(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "plain")
        (project.root / "theme.toml").unlink()
        with pytest.raises(ProjectError, match="no file 'theme.toml'"):
            project.build()


NOTEBOOK = importlib.util.find_spec("nbclient") is not None and importlib.util.find_spec("ipykernel") is not None


@pytest.mark.skipif(not NOTEBOOK, reason="needs the notebook extra (nbclient, ipykernel)")
class TestNotebook:
    def test_cli_build_runs_the_notebook(self, tmp_path: Path) -> None:
        project = svg.Project.new(tmp_path / "nb", notebook=True)
        assert project.config.entry == "main.ipynb:build" and not (project.root / "main.py").exists()
        cells = json.loads((project.root / "main.ipynb").read_text(encoding="utf-8"))["cells"]
        assert cells[-1]["source"] == "project = svg.Project.load()\nproject.preview()"
        assert not any('__name__ == "__main__"' in cell["source"] for cell in cells)
        written = project.build()
        assert [path.name for path in written] == ["nb.svg", "nb.png"]
        for path in written:
            check_output(path)

    def test_preview_inside_the_notebook(self, tmp_path: Path) -> None:
        import nbformat
        from nbclient import NotebookClient

        project = svg.Project.new(tmp_path / "scene", preset="animation", notebook=True)
        notebook = nbformat.read(project.root / "main.ipynb", as_version=4)
        NotebookClient(notebook, timeout=300, resources={"metadata": {"path": str(project.root)}}).execute()
        html = notebook.cells[-1].outputs[0]["data"]["text/html"]
        assert html.count("<img") == 2 and "scene.gif" in html and "data:image/gif;base64" in html


class TestPreview:
    def test_preview_html(self, tmp_path: Path) -> None:
        shown = svg.Project.new(tmp_path / "card", preset="poster").preview(["svg", "pdf"])
        html = shown._repr_html_()
        assert [path.name for path in shown.paths] == ["card.svg", "card.pdf"]
        assert html.count("<img") == 2 and "card.pdf" in html and "Preview of 2 files" in repr(shown)

    def test_live_server_rebuilds(self, tmp_path: Path) -> None:
        import threading
        import time
        import urllib.request

        from svgwriter.tools.project._server import LiveServer

        project = svg.Project.new(tmp_path / "live")
        server = LiveServer(project.root, lambda values: svg.Project.load(project.root).build(["svg"]), "live", 0)
        thread = threading.Thread(target=server.serve, kwargs={"open_browser": False}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while server.version == 0 and time.monotonic() < deadline:
                time.sleep(0.05)
            page = urllib.request.urlopen(server.url).read().decode("utf-8")
            assert "live.svg" in page and "fetch('/version')" in page
            assert urllib.request.urlopen(server.url + "version").read() == b"1"
            main = project.root / "main.py"
            main.write_text(main.read_text(encoding="utf-8").replace("build(doc", "build(doc ", 1), encoding="utf-8")
            while server.version < 2 and time.monotonic() < deadline:
                time.sleep(0.05)
            assert server.version >= 2
            (project.root / "main.py").write_text("raise RuntimeError('broken on purpose')\n", encoding="utf-8")
            while "broken on purpose" not in server.page and time.monotonic() < deadline:
                time.sleep(0.05)
            assert "build failed" in server.page
        finally:
            server.close()
            thread.join(5)


class TestCli:
    def test_new_build_presets(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                               capsys: pytest.CaptureFixture[str]) -> None:
        from svgwriter.tools.cli import main

        monkeypatch.chdir(tmp_path)
        assert main(["presets"]) == 0
        assert "poster" in capsys.readouterr().out
        assert main(["new", "flyer", "--preset", "poster"]) == 0
        assert "svgwriter preview" in capsys.readouterr().out
        assert main(["build", "--path", "flyer", "--format", "svg"]) == 0
        assert capsys.readouterr().out.strip().endswith("flyer.svg")
        assert main(["new", "flyer", "--preset", "poster"]) == 2
        assert "not empty" in capsys.readouterr().err

    def test_build_outside_a_project(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                     capsys: pytest.CaptureFixture[str]) -> None:
        from svgwriter.tools.cli import main

        monkeypatch.chdir(tmp_path)
        assert main(["build"]) == 2
        assert "no svgwriter.toml" in capsys.readouterr().err

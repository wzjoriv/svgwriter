import warnings
from importlib import metadata

import pytest

import svgwriter as svg
from svgwriter._internal._presets import FONTS

from ..ops.test_fonts import _box_font

PLUGIN = "from pathlib import Path\n\ndef pack():\n    return [Path(__file__).with_name('pack')]\n"


@pytest.fixture
def clean_fonts():
    state = FONTS.state()
    yield
    FONTS.restore(state)


def _width(family: str) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return svg.ops.text_width("AA", family, 100)


def test_font_is_a_preset_kind():
    assert svg.preset.KINDS["font"] is FONTS is svg.preset.font
    assert FONTS.group == "svgwriter.font"


def test_registered_font_is_measured_and_unregistering_restores(clean_fonts):
    before = _width("SvgwPresetBox")
    assert svg.preset.font(_box_font("SvgwPresetBox")) == ["SvgwPresetBox"]
    assert _width("svgwpresetbox") == pytest.approx(140, abs=0.5)
    svg.preset.font.unregister("SvgwPresetBox")
    assert _width("SvgwPresetBox") == pytest.approx(before)


def test_registered_font_wins_over_installed_and_generic_names(clean_fonts):
    svg.preset.font(_box_font("Whatever"), name="serif")
    assert _width("serif") == pytest.approx(140, abs=0.5)


def test_taken_names_raise_unless_replaced(clean_fonts):
    svg.preset.font(_box_font("SvgwTaken"))
    with pytest.raises(ValueError, match="already registered"):
        svg.preset.font(_box_font("SvgwTaken"))
    assert svg.preset.font(_box_font("SvgwTaken"), replace=True) == ["SvgwTaken"]
    with pytest.raises(TypeError, match="call"):
        svg.preset.font.register()


def test_folders_group_files_by_family(clean_fonts, tmp_path):
    (tmp_path / "a.ttf").write_bytes(_box_font("SvgwFolderA"))
    (tmp_path / "b.ttf").write_bytes(_box_font("SvgwFolderB"))
    (tmp_path / "notes.txt").write_text("not a font", encoding="utf-8")
    assert svg.preset.font(tmp_path) == ["SvgwFolderA", "SvgwFolderB"]
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="no font files"):
        svg.preset.font(tmp_path / "empty")


def test_registered_font_renders_to_png_and_pdf(clean_fonts, tmp_path):
    def render(suffix: str) -> bytes:
        doc = svg.Document(120, 60)
        doc.text("AA", x=5, y=50, font_family="SvgwRenderBox", font_size=40)
        target = tmp_path / f"page{suffix}"
        doc.save(target)
        return target.read_bytes()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fallback = render(".png"), render(".pdf")
    svg.preset.font(_box_font("SvgwRenderBox"))
    assert render(".png") != fallback[0]
    assert render(".pdf") != fallback[1]


def test_plugins_load_from_entry_points(monkeypatch, tmp_path, clean_fonts):
    (tmp_path / "pack").mkdir()
    (tmp_path / "pack" / "box.ttf").write_bytes(_box_font("SvgwPluginBox"))
    (tmp_path / "svgwriter_fontpack.py").write_text(PLUGIN, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    point = metadata.EntryPoint("Plugin Box", "svgwriter_fontpack:pack", FONTS.group)
    monkeypatch.setattr(metadata, "entry_points", lambda group: [point] if group == FONTS.group else [])
    monkeypatch.setattr(FONTS, "_plugins_loaded", False)
    FONTS._changed()
    assert _width("Plugin Box") == pytest.approx(140, abs=0.5)
    assert "Plugin Box" in FONTS.list()

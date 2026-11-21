from __future__ import annotations

import dataclasses
import typing
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.__main__ import main
from svgwriter._document._constants import BUILTIN_SIZES, IDENTIFIER_SEPARATORS


class TestDocumentSize:
    def test_paper_in_millimetres(self) -> None:
        doc = svg.Document(size="a4")
        assert str(doc.root.get("width")) == "210mm" and str(doc.root.get("height")) == "297mm"
        box = doc.root.get("viewBox")
        assert (box.width, box.height) == (210.0, 297.0)

    def test_inches_and_pixels(self) -> None:
        letter = svg.Document(size="letter").root.get("viewBox")
        assert (letter.width, letter.height) == (8.5, 11.0)
        slide = svg.Document(size="slide-16:9").root
        assert slide.get("width").value == 1280 and slide.get("viewBox").height == 720

    @pytest.mark.parametrize(("name", "expected"), [
        ("a4-landscape", (297.0, 210.0)),
        ("a4-portrait", (210.0, 297.0)),
        ("business-card-portrait", (2.0, 3.5)),
        ("instagram-portrait", (1080.0, 1350.0)),
        ("instagram-portrait-landscape", (1350.0, 1080.0)),
    ])
    def test_orientation_suffixes(self, name: str, expected: tuple[float, float]) -> None:
        assert tuple(side.value for side in svg.page_size(name)) == expected

    def test_size_with_width_is_an_error(self) -> None:
        with pytest.raises(TypeError, match="either size= or width"):
            svg.Document(100, size="a4")

    def test_unknown_size_suggests(self) -> None:
        with pytest.raises(ValueError, match="did you mean 'a4'"):
            svg.Document(size="a44")
        with pytest.raises(ValueError, match="unknown size 'zzz'"):
            svg.page_size("zzz")

    def test_rendered_size_follows_units(self) -> None:
        pixels = svg.Document(size="a6").rasterize()
        assert pixels.shape[:2] == (560, 397)


class TestRegistry:
    def test_register_and_remove(self) -> None:
        added = svg.preset.size("square-card", "60mm", svg.mm(60))
        try:
            assert "square-card" in svg.preset.list("size")
            assert svg.preset.get("size", "square-card") == added == svg.PageSize(60.0, 60.0, svg.Unit.MM)
            assert str(svg.page_size("square-card")[0]) == "60mm"
            with pytest.raises(ValueError, match="already registered"):
                svg.preset.size("square-card", 1, 1)
            assert svg.preset.size("square-card", 1, 2, replace=True).height == 2.0
        finally:
            svg.preset.unregister("size", "square-card")
        with pytest.raises(KeyError):
            svg.preset.unregister("size", "square-card")

    def test_builtin_is_replaced_not_removed(self) -> None:
        with pytest.raises(KeyError, match="built in"):
            svg.preset.unregister("size", "a4")

    def test_units_must_match(self) -> None:
        with pytest.raises(ValueError, match="one unit"):
            svg.preset.size("mixed", "10mm", "2in")

    def test_cli_lists_sizes(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["sizes"]) == 0
        out = capsys.readouterr().out
        assert "a4" in out and "210mm x 297mm" in out and "slide-16:9" in out


class TestPageSize:
    def test_orientation(self) -> None:
        a4 = svg.size.a4
        assert (a4.width, a4.height, a4.units) == (210.0, 297.0, svg.Unit.MM)
        assert (a4.landscape.width, a4.landscape.height) == (297.0, 210.0)
        assert a4.landscape.landscape == a4.landscape and a4.landscape.portrait == a4
        assert svg.size.slide_16_9.portrait.height == 1280.0

    def test_document_scene_and_project_take_a_page_size(self, tmp_path: Path) -> None:
        box = svg.Document(size=svg.size.letter.landscape).root.get("viewBox")
        assert (box.width, box.height) == (11.0, 8.5)

        class Story(svg.Scene):
            size = svg.size.instagram_story

        assert (Story.width, Story.height) == (1080.0, 1920.0)
        (tmp_path / "svgwriter.toml").write_text('[project]\nname = "demo"\nsize = "icon"\n')
        config = svg.Project.load(tmp_path).config
        assert config.size == "icon"
        assert dataclasses.replace(config, size=svg.size.icon).size.width == 512.0

    def test_namespace_names_are_identifiers(self) -> None:
        assert svg.size.slide_16_9 == svg.preset.get("size", "slide-16:9")
        assert svg.size.business_card.units is svg.Unit.IN
        with pytest.raises(AttributeError, match="no size 'nope'"):
            _ = svg.size.nope

    def test_namespace_follows_registrations(self) -> None:
        svg.preset.size("poster-50x70", "50cm", "70cm")
        try:
            assert svg.size.poster_50x70.portrait.height == 70.0
            assert "poster_50x70" in dir(svg.size)
        finally:
            svg.preset.unregister("size", "poster-50x70")
        assert "poster_50x70" not in dir(svg.size)

    def test_static_attributes_cover_the_builtins(self) -> None:
        declared = set(typing.get_type_hints(type(svg.size), localns={"PageSize": svg.PageSize}))
        assert declared == {IDENTIFIER_SEPARATORS.sub("_", name).strip("_") for name in BUILTIN_SIZES}


class TestScene:
    def test_named_size_sets_width_and_height(self) -> None:
        class Story(svg.Scene):
            size = "instagram-story"

        assert (Story.width, Story.height) == (1080.0, 1920.0)
        assert Story().document.root.get("viewBox").height == 1920.0

    def test_subclass_width_overrides_inherited_size(self) -> None:
        class Base(svg.Scene):
            size = "favicon"

        class Wide(Base):
            width, height = 50, 20

        assert Wide.size is None and Wide().document.root.get("width") == 50

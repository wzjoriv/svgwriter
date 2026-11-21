from __future__ import annotations

import warnings

import numpy as np
import pytest

import svgwriter as svg
from tests.conftest import wellformed

CATALOGUES = {"pattern": svg.patterns, "filter": svg.filters, "gradient": svg.gradients, "marker": svg.markers,
              "text_effect": svg.text_effects}
ENTRIES = [(kind, name) for kind, module in CATALOGUES.items() for name in module.__all__]


def _drawing(kind: str, name: str) -> svg.Document:
    doc = svg.Document(160, 60)
    preset = getattr(CATALOGUES[kind], name)
    if kind in ("pattern", "gradient"):
        doc.rect(10, 10, 140, 40, fill=preset())
    elif kind == "filter":
        with doc.group() as group:
            doc.circle(60, 30, 14, fill="teal")
            doc.circle(84, 30, 14, fill="orange")
        group.filter = preset()
    elif kind == "marker":
        doc.path("M10 50 L80 10 L150 50", fill="none", stroke="black", stroke_width=2, marker_start=preset(),
                 marker_mid=preset(), marker_end=preset())
    else:
        line = doc.text("Hot sparks", x=10, y=40, font_size=26)
        preset(line[4:10])
    return doc


@pytest.mark.parametrize(("kind", "name"), ENTRIES)
class TestEveryPreset:
    def test_listed_and_named(self, kind: str, name: str) -> None:
        assert name in svg.preset.list(kind)
        assert getattr(CATALOGUES[kind], name) is svg.preset.get(kind, name)

    def test_writes_wellformed_svg(self, kind: str, name: str) -> None:
        wellformed(_drawing(kind, name).to_string())

    def test_renders_png(self, kind: str, name: str) -> None:
        pixels = np.asarray(_drawing(kind, name).rasterize())
        assert pixels[..., 3].sum() > 0

    @pytest.mark.parametrize("extension", ["pdf", "pptx"])
    def test_exports(self, kind: str, name: str, extension: str, tmp_path) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            _drawing(kind, name).save(tmp_path / f"out.{extension}")
        assert (tmp_path / f"out.{extension}").stat().st_size > 0


class TestCatalogues:
    def test_unknown_name_suggests(self) -> None:
        with pytest.raises(AttributeError, match="did you mean 'stripes'"):
            svg.patterns.stripe  # noqa: B018

    def test_user_presets_join_their_catalogue(self) -> None:
        @svg.preset.pattern
        def bricks(size: float = 4) -> svg.Pattern:
            return svg.Pattern(svg.rect(0, 0, size, size / 2), width=size, height=size)

        try:
            assert svg.patterns.bricks is bricks and "bricks" in dir(svg.patterns)
        finally:
            svg.preset.unregister("pattern", "bricks")
        assert "bricks" not in dir(svg.patterns)

    def test_replacing_a_builtin_answers_with_the_replacement(self) -> None:
        @svg.preset.filter(name="blur", replace=True)
        def sharp() -> svg.Filter:
            return svg.Filter()

        try:
            assert svg.filters.blur is sharp
        finally:
            svg.preset.unregister("filter", "blur")
        assert svg.filters.blur is not sharp

    @pytest.mark.parametrize("kind", ["pattern", "filter", "gradient", "marker"])
    def test_wrong_return_type_fails_loudly(self, kind: str) -> None:
        decorator = getattr(svg.preset, kind)

        @decorator(name="broken")
        def broken() -> svg.Element:
            return svg.circle(0, 0, 1)

        try:
            with pytest.raises(TypeError, match=f"{kind} 'broken' returned Circle"):
                broken()
        finally:
            svg.preset.unregister(kind, "broken")

    def test_taken_name_names_the_owner(self) -> None:
        with pytest.raises(ValueError, match="built in"):
            svg.preset.marker(name="arrow")(lambda: svg.Marker())

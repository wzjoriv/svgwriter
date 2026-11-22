from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.errors import ThemeError
from svgwriter.model.theme.sheet import STYLE_ID


def _themed(theme: str = "dark") -> svg.Document:
    doc = svg.Document(60, 40, theme=theme)
    doc.rect(0, 0, 60, 40).as_role("background")
    doc.rect(10, 10, 40, 20).as_role("box")
    doc.circle(30, 20, 4).as_role("dot")
    return doc


def _inline(theme: str = "dark") -> svg.Document:
    styles = svg.themes.get(theme)
    doc = svg.Document(60, 40)
    doc.rect(0, 0, 60, 40, style=styles.style("background"))
    doc.rect(10, 10, 40, 20, style=styles.style("box"))
    doc.circle(30, 20, 4, style=styles.style("dot"))
    return doc


class TestSheet:
    def test_only_used_roles_and_tree_restored(self) -> None:
        doc = _themed()
        text = doc.to_string()
        assert f'<style id="{STYLE_ID}"' in text and ".role-dot" in text and ".role-title" not in text
        assert [e.tag for e in doc.root] == ["rect", "rect", "circle"]

    def test_nothing_written_without_roles(self) -> None:
        doc = svg.Document(10, 10, theme="dark")
        doc.circle(5, 5, 2)
        assert "<style" not in doc.to_string()

    def test_title_stays_first(self) -> None:
        doc = _themed()
        doc.title("Chart")
        assert [e.tag for e in svg.parse(doc.to_string())][:2] == ["title", "style"]

    def test_restyle_parsed_document(self) -> None:
        parsed = svg.Document.from_string(_themed("dark").to_string(), theme="light")
        text = parsed.to_string()
        assert text.count("<style") == 1 and svg.themes.get("light").palette.surface.hex in text
        assert svg.themes.get("dark").palette.surface.hex in str(parsed.root[0])

    def test_unknown_role_class(self) -> None:
        doc = svg.Document(10, 10)
        doc.circle(5, 5, 2, class_="role-nope")
        with pytest.raises(ThemeError, match="no such role"):
            doc.to_string()

    def test_explicit_attributes_win(self) -> None:
        doc = svg.Document(20, 20, theme="dark")
        doc.rect(0, 0, 20, 20, fill="#ff0000").as_role("box")
        pixel = doc.rasterize()[10, 10]
        assert tuple(pixel[:3]) == (1.0, 0.0, 0.0)

    def test_theme_setter_and_context(self) -> None:
        doc = _themed()
        doc.theme = svg.themes.get("paper")
        assert svg.themes.get("paper").palette.surface.hex in doc.to_string()
        with svg.themes.get("print"):
            assert svg.Document().theme.name == "print"


class TestRenderers:
    @pytest.mark.parametrize("theme", ["light", "dark", "paper", "print", "mono"])
    def test_png_matches_inline_styles(self, theme: str) -> None:
        assert np.array_equal(_themed(theme).rasterize(), _inline(theme).rasterize())

    def test_pdf_matches_inline_styles(self) -> None:
        pytest.importorskip("skia")
        themed, inline = _themed().export("pdf"), _inline().export("pdf")
        assert isinstance(themed, bytes) and len(themed) == len(inline)

    def test_pptx_carries_colors(self) -> None:
        pytest.importorskip("pptx")
        import io

        from pptx import Presentation

        data = _themed().export("pptx")
        shapes = Presentation(io.BytesIO(data)).slides[0].shapes  # type: ignore[arg-type]
        fills = {str(s.fill.fore_color.rgb) for s in shapes if s.fill.type is not None}
        assert {"111827", "1F2937", "B45309"} <= fills

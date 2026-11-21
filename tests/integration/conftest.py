"""Shared pieces of the cross-feature tests: a laid-out, themed card and generated font files."""

from __future__ import annotations

from pathlib import Path

import pytest

import svgwriter as svg
from tests.ops.test_typeface import _font

GLYPH = 400
"""Width of the generated fonts' ``A`` box in font units; its advance is 100 more."""
BOLD_GLYPH = 600


def card(theme: str = "light") -> tuple[svg.Document, svg.VStack]:
    """A document holding a card: a title, body text and a bar stacked on a ``surface`` background."""
    doc = svg.Document(240, 160, theme=theme)
    stack = svg.VStack(svg.text("Heading").as_role("title"), svg.text("Body copy").as_role("text"),
                       svg.rect(0, 0, 60, 8).as_role("accent"), gap=6, padding=10, background="surface")
    stack.translate(12, 16)
    doc += stack
    return doc, stack


@pytest.fixture
def font_files(tmp_path: Path) -> list[Path]:
    """Regular and bold faces of the family ``SvgwIntegration`` on disk."""
    paths = []
    for name, width, weight in (("regular", GLYPH, 400), ("bold", BOLD_GLYPH, 700)):
        path = tmp_path / f"Integration-{name}.ttf"
        path.write_bytes(_font("SvgwIntegration", width, weight=weight))
        paths.append(path)
    return paths


@pytest.fixture
def typeface(font_files: list[Path]) -> svg.Typeface:
    return svg.Typeface.from_files(*font_files)

from __future__ import annotations

from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.theme import ThemeError


@pytest.mark.parametrize("name", ["light", "dark", "paper", "print", "mono"])
def test_round_trip(name: str, tmp_path: Path) -> None:
    theme = svg.Theme.get(name).replace(roles={"badge": {"fill": "{palette.accent}"}})
    path = tmp_path / "theme.toml"
    theme.save(path)
    assert svg.Theme.load(path) == theme


def test_extends_references_and_nested_roles() -> None:
    theme = svg.Theme.from_toml("""
name = "brand"
extends = "paper"

[palette]
primary = "#123456"
accent = "{palette.primary}"

[fonts]
family = "Georgia, serif"

[fonts.sizes]
title = 30

[roles.arrow.head]
fill = "{palette.accent}"

[roles."arrow.line"]
stroke-width = 3

[roles.label]
font-size = "{fonts.sizes.title}"
""")
    assert theme.name == "brand" and theme.palette.background == svg.Theme.get("paper").palette.background
    assert theme.style("arrow.head")["fill"].hex == "#123456"
    assert theme.style("arrow.line")["stroke-width"] == "3px"
    assert theme.style("label")["font-size"] == "30px" and theme.fonts.family == "Georgia, serif"


def test_quoted_keys_written() -> None:
    text = svg.Theme.get("light").replace(roles={"arrow.tip": {"fill": "red"}}).to_toml()
    assert '[roles."arrow.tip"]' in text and "[fonts.sizes]" in text


@pytest.mark.parametrize(("text", "message"), [
    ("colour = 1", "unknown theme file keys"),
    ('extends = "nope"', "unknown theme 'nope'"),
    ("[palette]\nprimary = true", "palette.primary: unsupported value"),
    ('[palette]\na = "{palette.b}"\nb = "{palette.a}"', "cycle"),
    ('[palette]\nprimary = "{palette.nothing}"', "unknown reference"),
    ("[fonts]\nstyle = 1", "unknown font keys"),
    ("[fonts]\nsizes = 3", "fonts.sizes: expected a table"),
    ("palette = 3", "palette: expected a table"),
    ("[roles]\nfill = \"red\"", "need a role table"),
    ("[roles.box]\nfill = [1]", "roles.box.fill: unsupported value"),
    ('[roles.box]\nfill = "{palette.nope}"', "unknown reference"),
    ("name = ", "invalid theme file"),
])
def test_errors(text: str, message: str) -> None:
    with pytest.raises(ThemeError, match=message):
        svg.Theme.from_toml(text)

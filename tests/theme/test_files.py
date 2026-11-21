from __future__ import annotations

from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.errors import ThemeError


@pytest.mark.parametrize("name", ["light", "dark", "paper", "print", "mono"])
def test_round_trip(name: str, tmp_path: Path) -> None:
    theme = svg.themes.get(name).replace(roles={"badge": {"fill": "{palette.accent}"}})
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
    assert theme.name == "brand" and theme.palette.background == svg.themes.get("paper").palette.background
    assert theme.style("arrow.head")["fill"].hex == "#123456"
    assert theme.style("arrow.line")["stroke-width"] == "3px"
    assert theme.style("label")["font-size"] == "30px" and theme.fonts.family == "Georgia, serif"


def test_quoted_keys_written() -> None:
    text = svg.themes.get("light").replace(roles={"arrow.tip": {"fill": "red"}}).to_toml()
    assert text == 'name = "light"\nextends = "light"\n\n[roles."arrow.tip"]\nfill = "red"\n'


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
    ("[roles.box]\nfill = [1]", "roles.box.fill: a color array holds 3 or 4 numbers"),
    ("[roles.box]\nfill = true", "roles.box.fill: unsupported value"),
    ("[palette]\nprimary = [1, 0.5, 0]", "not a mix"),
    ("[palette]\nprimary = [256, 0, 0]", "0 to 255"),
    ("[palette]\nprimary = [1.5, 0.0, 0.0]", "0 to 1"),
    ("[roles.box]\nstroke-width = inf", "not a finite number"),
    ('[fonts.sizes]\ntext = "big"', "fonts.sizes.text: expected a number"),
    ("[fonts]\nfamily = 3", "fonts.family: expected text"),
    ('[roles.box]\nfill = "{palette.nope}"', "unknown reference"),
    ("name = ", "invalid theme file"),
])
def test_errors(text: str, message: str) -> None:
    with pytest.raises(ThemeError, match=message):
        svg.Theme.from_toml(text)


NIGHT = """# Night: a darker brand theme
name = "night"  # shown in menus
extends = "dark"

[palette]
# brand colours
primary = "#38bdf8"   # sky
accent = "{palette.primary}"
secondary = [255, 128, 0]

[fonts.sizes]
title = 26

[roles.arrow.head]
fill = "{palette.accent}"  # the tip
"""


def test_unchanged_file_saves_verbatim(tmp_path: Path) -> None:
    path = tmp_path / "night.toml"
    path.write_text(NIGHT, encoding="utf-8")
    theme = svg.Theme.load(path)
    assert theme.extends == "dark" and theme.palette.secondary.hex == "#ff8000"
    theme.save(path)
    assert path.read_text(encoding="utf-8") == NIGHT


def test_edit_changes_only_edited_keys() -> None:
    theme = svg.Theme.from_toml(NIGHT).replace(
        palette={"primary": "#ff0000"}, fonts={"sizes": {"caption": 10}},
        roles={"arrow.head": {"stroke": "{palette.border}"}, "badge": {"fill": "{palette.secondary}"}})
    text = theme.to_toml()
    assert text == NIGHT.replace('"#38bdf8"', '"#ff0000"').replace(
        "title = 26\n", "title = 26\ncaption = 10\n").replace(
        '# the tip\n', '# the tip\nstroke = "{palette.border}"\n') + '\n[roles.badge]\nfill = "{palette.secondary}"\n'
    assert svg.Theme.from_toml(text) == theme


def test_name_and_extends_kept() -> None:
    theme = svg.Theme.from_toml('extends = "paper"\n').replace(name="sepia")
    assert theme.to_toml() == 'extends = "paper"\nname = "sepia"\n'
    assert svg.Theme.from_toml("[palette]\nprimary = \"red\"\n").to_toml() == "[palette]\nprimary = \"red\"\n"


def test_references_kept_and_functions_resolved() -> None:
    theme = svg.themes.get("dark").replace(
        name="night", palette={"accent": "{palette.primary}", "glow": lambda p: p.primary.with_alpha(0.5)},
        roles={"badge": {"fill": "{palette.glow}", "stroke-width": lambda t: t.fonts.sizes["caption"] / 5}})
    text = theme.to_toml()
    assert 'extends = "dark"' in text and 'accent = "{palette.primary}"' in text
    assert 'glow = [0.6, 0.9647058823529412, 0.8941176470588236, 0.5]' in text and "stroke-width = 2.2" in text
    assert svg.Theme.from_toml(text) == theme


def test_variant_of_registered_variant_extends_it() -> None:
    svg.themes.register(svg.themes.get("light").replace(name="brand-test", palette={"primary": "navy"}))
    try:
        variant = svg.themes.get("brand-test").replace(name="brand-2")
        assert svg.themes.get("brand-test").extends == "light" and variant.extends == "brand-test"
        assert variant.to_toml() == 'name = "brand-2"\nextends = "brand-test"\n'
    finally:
        svg.themes.unregister("brand-test")


def test_unregistered_theme_written_in_full() -> None:
    theme = svg.Theme("site", dict(svg.themes.get("paper").palette.sources), roles={"hero": {"fill": "red"}})
    text = theme.to_toml()
    assert "extends" not in text and "[palette]" in text and "[roles.hero]" in text
    assert svg.Theme.from_toml(text) == theme


def test_missing_base_and_file_errors(tmp_path: Path) -> None:
    svg.themes.register(svg.themes.get("light").replace(name="gone-test"))
    variant = svg.themes.get("gone-test").replace(name="child")
    svg.themes.unregister("gone-test")
    with pytest.raises(ThemeError, match="extends: unknown theme 'gone-test'"):
        variant.to_toml()
    path = tmp_path / "broken.toml"
    path.write_text('[palette]\nprimary = "{palette.nope}"\n', encoding="utf-8")
    with pytest.raises(ThemeError, match=r"broken\.toml: palette\.primary: unknown reference"):
        svg.Theme.load(path)


def test_expressions_saved_as_written() -> None:
    text = '[palette]\nprimary = "#fde68a"\nlabel = "=readable({palette.primary})"  # follows primary\n'
    theme = svg.Theme.from_toml(text)
    assert theme.palette.label.hex == "#000000"
    darker = theme.replace(palette={"primary": "#1e3a8a"})
    saved = darker.to_toml()
    assert saved == text.replace("#fde68a", "#1e3a8a")
    assert svg.Theme.from_toml(saved).palette.label.hex == "#ffffff"

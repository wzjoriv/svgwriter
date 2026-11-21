from __future__ import annotations

import threading

import pytest

import svgwriter as svg
from svgwriter.errors import ThemeError
from svgwriter.model.theme import Fonts, Palette

BUILTINS = ("light", "dark", "paper", "print", "mono", "noir", "brutalist", "dracula", "alucard", "one-dark",
            "one-light")
AA_TEXT = 4.5
AA_LARGE_TEXT = 3.0
LARGE_TEXT_PX = 24.0


class TestPalette:
    def test_literals_references_and_functions(self) -> None:
        p = Palette({"ink": "black", "paper": "#ffffff", "edge": "{palette.ink}", "mid": lambda p: p.ink.mix(p.paper)})
        assert p.edge.hex == "#000000" and p["mid"].hex == "#808080"
        assert list(p) == ["ink", "paper", "edge", "mid"] and len(p) == 4

    def test_replace_rederives(self) -> None:
        p = Palette({"a": "red", "b": lambda p: p.a.darken(0.1)}).replace(a="blue")
        assert p.b.hex == svg.Color.parse("blue").darken(0.1).hex

    @pytest.mark.parametrize(("sources", "message"), [
        ({"a": "{palette.missing}"}, "unknown reference"),
        ({"a": "{fonts.family}"}, "unknown reference"),
        ({"a": "{palette.b}", "b": "{palette.a}"}, "cycle: palette.a -> palette.b -> palette.a"),
        ({"a": lambda p: p.a}, "cycle"),
        ({"a": lambda p: p.nothing}, "unknown palette role"),
        ({"a": "not a color"}, "palette.a"),
    ])
    def test_errors(self, sources: dict[str, object], message: str) -> None:
        with pytest.raises(ThemeError, match=message):
            Palette(sources)  # type: ignore[arg-type]

    def test_attribute_access(self) -> None:
        p = Palette({"a": "red"})
        assert not hasattr(p, "b")
        with pytest.raises(AttributeError):
            _ = p._hidden
        assert p == Palette({"a": "#ff0000"}) and p != Palette({"a": "blue"})
        assert "a" in repr(p) and p.sources == {"a": "red"}


class TestFonts:
    def test_defaults_and_replace(self) -> None:
        fonts = Fonts().replace(monospace="Mono", weights={"light": 300})
        assert fonts.monospace == "Mono" and fonts.weights["light"] == 300 and fonts.weights["bold"] == 700
        assert fonts.lookup("family") == Fonts().family

    @pytest.mark.parametrize("path", ["sizes.huge", "nothing", "family.x"])
    def test_unknown_lookup(self, path: str) -> None:
        with pytest.raises(ThemeError, match="unknown font value"):
            Fonts().lookup(path)


class TestTheme:
    @pytest.mark.parametrize("name", BUILTINS)
    def test_builtins_resolve_every_role(self, name: str) -> None:
        theme = svg.themes.get(name)
        assert theme.name == name and set(svg.themes.list()) >= set(BUILTINS)
        for role in theme.roles:
            assert theme.style(role)

    @pytest.mark.parametrize("name", BUILTINS)
    def test_builtin_text_meets_wcag_aa(self, name: str) -> None:
        theme = svg.themes.get(name)
        p = theme.palette

        def contrast(a: svg.Color, b: svg.Color) -> float:
            low, high = sorted((a.luminance, b.luminance))
            return (high + 0.05) / (low + 0.05)

        for role in theme.roles:
            style = theme.style(role)
            if "font-family" not in style:
                continue
            grounds = (p.primary,) if role == "label" else (p.background, p.surface)
            large = float(str(style["font-size"]).removesuffix("px")) >= LARGE_TEXT_PX
            for ground in grounds:
                assert contrast(style["fill"], ground) >= (AA_LARGE_TEXT if large else AA_TEXT), (role, ground.hex)

    @pytest.mark.parametrize("name", BUILTINS)
    def test_builtin_themes_are_distinct(self, name: str) -> None:
        styles = {other: (svg.themes.get(other).style("title")["fill"].hex, svg.themes.get(other).palette.surface.hex)
                  for other in BUILTINS}
        assert list(styles.values()).count(styles[name]) == 1

    def test_immutable(self) -> None:
        with pytest.raises(AttributeError, match="immutable"):
            svg.themes.get("light").name = "x"  # type: ignore[misc]

    def test_derived_entries_follow_foreground(self) -> None:
        light = svg.themes.get("light")
        red = light.replace(palette={"foreground": "#ff0000"})
        assert red.palette.border != light.palette.border
        assert red.style("text")["fill"].hex == "#ff0000"

    def test_role_property_merge_and_function_roles(self) -> None:
        theme = svg.themes.get("light").replace(roles={
            "box": {"stroke-dasharray": "4 2"},
            "badge": lambda t: {"fill": t.palette.accent, "stroke": "{palette.border}"},
            "note": {"font": lambda t: f"{t.fonts.sizes['caption']}px serif"},
        })
        assert theme.style("box")["stroke-dasharray"] == "4 2" and theme.style("box")["stroke-width"] == "1px"
        assert theme.style("badge")["fill"] == theme.palette.accent
        assert theme.style("note")["font"] == "11.0px serif"

    def test_embedded_reference_and_alpha(self) -> None:
        theme = svg.themes.get("mono").replace(palette={"shade": lambda p: p.foreground.with_alpha(0.25)},
                                              roles={"shade": {"fill": "{palette.shade}", "filter": "url(#{fonts.sizes.text})"}})
        style = theme.style("shade")
        assert style["fill-opacity"] == 0.25 and style["filter"] == "url(#14.0)"

    @pytest.mark.parametrize(("roles", "message"), [
        ({"Bad Name": {}}, "invalid role name"),
        ({"x": {"fill": "{palette.nope}"}}, "roles.x.fill: unknown reference"),
        ({"x": {"fill": "{other.nope}"}}, "use {palette.name}"),
        ({"x": {"fill": "{fonts.sizes.nope}"}}, "unknown reference"),
        ({"x": {"fill": [1, 2]}}, "unsupported value"),
        ({"x": 3}, "expected a mapping"),
        ({"x": lambda t: t.nothing}, "roles.x"),
        ({"x": {"fill": lambda t: t.nothing}}, "roles.x.fill"),
    ])
    def test_role_errors(self, roles: dict[str, object], message: str) -> None:
        with pytest.raises(ThemeError, match=message):
            svg.themes.get("light").replace(roles=roles)  # type: ignore[arg-type]

    def test_css_and_unknown_role(self) -> None:
        theme = svg.themes.get("light")
        assert len(theme.css()) == len(theme.roles)
        assert [s for s, _ in theme.css(["dot", "box"])] == [".role-box", ".role-dot"]
        with pytest.raises(ThemeError, match="no role"):
            theme.css(["nope"])
        with pytest.raises(ThemeError, match="no role"):
            theme.style("nope")

    def test_of_and_equality(self) -> None:
        dark = svg.themes.get("dark")
        assert svg.Theme.of(dark) is dark and svg.Theme.of("dark") is dark
        with pytest.raises(TypeError):
            svg.Theme.of(3)  # type: ignore[arg-type]
        with pytest.raises(KeyError):
            svg.themes.get("nope")
        assert dark == dark.replace() and dark != svg.themes.get("light") and dark != "dark"
        assert repr(dark) == "Theme('dark')"

    def test_custom_theme_from_scratch(self) -> None:
        palette = dict(svg.themes.get("light").palette.sources)
        theme = svg.Theme("site", palette, Fonts(family="Georgia"), roles={"hero": {"fill": "{palette.primary}"}})
        assert theme.style("text")["font-family"] == "Georgia" and "hero" in theme.roles


class TestContext:
    def test_nested_blocks(self) -> None:
        dark, paper = svg.themes.get("dark"), svg.themes.get("paper")
        with dark:
            with paper:
                assert svg.Theme.current() is paper and svg.Document().theme is paper
            with dark:
                assert svg.Theme.current() is dark
            assert svg.Theme.current() is dark
        assert svg.Theme.current().name == "light"

    def test_threads_are_independent(self) -> None:
        seen: list[str] = []
        with svg.themes.get("dark"):
            worker = threading.Thread(target=lambda: seen.append(svg.Theme.current().name))
            worker.start()
            worker.join()
        assert seen == ["light"]

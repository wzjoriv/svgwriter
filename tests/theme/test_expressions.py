from __future__ import annotations

from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.theme import Palette, ThemeError
from svgwriter.theme._constants import MAX_EXPRESSION_DEPTH, MAX_EXPRESSION_LENGTH, MAX_REFERENCE_DEPTH
from svgwriter.theme._expression import evaluate, is_expression

LIGHT = svg.Theme.get("light")
SIZES = {"fonts.sizes.text": 14.0, "fonts.sizes.caption": 11.0}


def palette_value(expression: str) -> svg.Color:
    return Palette({**LIGHT.palette.sources, "x": expression}).x


def role_value(expression: str, prop: str = "opacity") -> object:
    return LIGHT.replace(roles={"probe": {prop: expression}}).style("probe")[prop]


def value(expression: str) -> object:
    return evaluate(expression, SIZES.__getitem__, "test")


class TestColors:
    @pytest.mark.parametrize(("expression", "expected"), [
        ("lighten(#204060, 0.2)", svg.Color.parse("#204060").lighten(0.2)),
        ("darken(navy, 0.5)", svg.Color.parse("navy").darken(0.5)),
        ("mix(red, blue)", svg.Color.parse("red").mix("blue")),
        ("mix(red, blue, 0.25, 'oklch')", svg.Color.parse("red").mix("blue", 0.25, "oklch")),
        ('mix(red, blue, 0.25, "oklab")', svg.Color.parse("red").mix("blue", 0.25, "oklab")),
        ("alpha(oklch(62.8% 0.2577 29.23), 0.5)", svg.Color.parse("oklch(62.8% 0.2577 29.23)").with_alpha(0.5)),
        ("saturate(hsl(200, 40%, 50%), 0.3)", svg.Color.parse("hsl(200, 40%, 50%)").saturate(0.3)),
        ("desaturate(rgb(200 30 30 / 0.5), 0.3)", svg.Color.parse("rgb(200 30 30 / 0.5)").desaturate(0.3)),
        ("hue_shift(#ff0000, 120)", svg.Color.parse("#ff0000").hue_shift(120)),
        ("complement(teal)", svg.Color.parse("teal").complement()),
        ("grayscale(color(display-p3 1 0 0))", svg.Color.parse("color(display-p3 1 0 0)").grayscale()),
        ("invert(device-cmyk(0 1 1 0))", svg.Color.parse("device-cmyk(0 1 1 0)").invert()),
        ("readable(#fbbf24)", svg.Color.parse("#fbbf24").readable()),
        ("readable(#fbbf24, '#1f2933', white)", svg.Color.parse("#fbbf24").readable("#1f2933", "white")),
        ("if(is_dark(#111111), white, black)", svg.Color.parse("white")),
    ])
    def test_functions(self, expression: str, expected: svg.Color) -> None:
        assert palette_value(expression) == expected

    def test_references_follow_their_source(self) -> None:
        palette = Palette({"ink": "#0f766e", "paper": "white", "label": "readable({palette.ink})",
                           "edge": "mix({palette.ink}, {palette.paper}, 0.6, 'oklab')"})
        assert palette.label.hex == "#ffffff"
        assert palette.replace({"ink": "#fde68a"}).label.hex == "#000000"
        assert palette.edge == svg.Color.parse("#0f766e").mix("white", 0.6, "oklab")

    def test_builtin_derived_entries(self) -> None:
        sources = LIGHT.palette.sources
        assert sources["on_primary"] == "readable({palette.primary}, {palette.background}, {palette.foreground})"
        assert LIGHT.palette.on_primary.hex == "#ffffff" and svg.Theme.get("dark").palette.on_primary.hex == "#042f2e"
        assert LIGHT.palette.border == LIGHT.palette.foreground.mix(LIGHT.palette.background, 0.7)
        assert LIGHT.palette.shadow == LIGHT.palette.foreground.with_alpha(0.2)


class TestNumbersAndLogic:
    @pytest.mark.parametrize(("expression", "expected"), [
        ("{fonts.sizes.text} * 1.5", 21.0),
        ("({fonts.sizes.text} + 2) / 4", 4.0),
        ("-{fonts.sizes.caption} + 1", -10.0),
        ("2px * 3", 6),
        ("min(3, 1, 2)", 1), ("max(3, 1, 2)", 3), ("clamp(15, 0, 10)", 10),
        ("round(2.345, 2)", 2.35), ("round(2.5)", 2),
        ("luminance(white)", 1.0), ("round(contrast(white, black))", 21),
        ("is_light(white)", True), ("is_dark(white)", False),
        ("1 < 2 and 2 <= 2 and 3 > 2 and 3 >= 3", True),
        ("1 == 2 or 'a' != 'b'", True), ("not (1 == 1)", False), ("red == #ff0000", True),
        ("if({fonts.sizes.text} > 12, 'large', 'small')", "large"),
        ("if(true, 1, 1 / 0)", 1), ("false or true and false", False),
    ])
    def test_values(self, expression: str, expected: object) -> None:
        assert value(expression) == expected

    def test_role_values(self) -> None:
        assert role_value("{fonts.sizes.text} * 1.5", "font-size") == "21px"
        assert role_value("if(is_dark({palette.background}), 0.4, 0.2)") == 0.2
        assert role_value("lighten({palette.primary}, 0.5)", "fill") == LIGHT.palette.primary.lighten(0.5)
        assert role_value("alpha({palette.primary}, 0.25)", "fill").a == 0.25


class TestText:
    @pytest.mark.parametrize("text", [
        "1px solid {palette.border}", "Gill Sans, sans-serif", "4 2", "-0.02em", "50%", "2px", "url(#a-b)",
        "rotate(45 10 10)", "rgb(255 0 0 / 50%)", "#ff000080", "none", "small-caps", "{fonts.sizes.text}px",
    ])
    def test_plain_text_is_not_an_expression(self, text: str) -> None:
        assert not is_expression(text)

    def test_text_keeps_references(self) -> None:
        assert role_value("1px solid {palette.border}", "border") == f"1px solid {LIGHT.palette.border.hex}"
        assert role_value("Gill Sans, sans-serif", "font-family") == "Gill Sans, sans-serif"


HOSTILE = [
    ("__import__('os')", "unexpected character '_'"),
    ("__import__('os').system('echo hacked')", "unexpected character '_'"),
    ("().__class__", "unexpected character '.'"),
    ("().__class__.__bases__[0].__subclasses__()", "unexpected character '.'"),
    ("a.b()", "unexpected character '.'"),
    ("{palette.primary}.__class__", "unexpected character '.'"),
    ("{palette.__class__}", "unknown reference"),
    ("{palette.primary.__class__}", "unknown reference"),
    ("eval('1 + 1')", "unknown function 'eval'"),
    ("exec('x = 1')", "unknown function 'exec'"),
    ("open('secrets.txt')", "unknown function 'open'"),
    ("getattr(red, 'hex')", "unknown function 'getattr'"),
    ("compile('1', 'x', 'eval')", "unknown function 'compile'"),
    ("lambda: 0", "lambda: 0"),
    ("9**9**9", r"power operator \*\* is not supported"),
    ("2 ** 1000", r"power operator \*\* is not supported"),
    ("9e999", "exponent notation is not allowed"),
    ("1e308 * 10", "exponent notation is not allowed"),
    ("{fonts.sizes.text} * 1E9", "exponent notation is not allowed"),
    ("9" * 400 + " + 1", "number too large"),
    ("1000 * 1000 * 1000", "number too large"),
    ("'%s' % 'x'", "% operator is not supported"),
    ("'%(a)s' % {palette.primary}", "% operator is not supported"),
    ("'{0.__class__}'.format(red)", "unexpected character '.'"),
    ("f'{palette.primary}' + 1", "unknown name 'f'"),
    ("(" * (MAX_EXPRESSION_DEPTH + 1) + "1" + ")" * (MAX_EXPRESSION_DEPTH + 1), "nested deeper than"),
    ("-" * (MAX_EXPRESSION_DEPTH + 1) + "1", "nested deeper than"),
    ("not " * (MAX_EXPRESSION_DEPTH + 1) + "true", "nested deeper than"),
    ("1 + " * MAX_EXPRESSION_LENGTH + "1", f"longer than {MAX_EXPRESSION_LENGTH} characters"),
    ("x" * (MAX_EXPRESSION_LENGTH + 1), f"longer than {MAX_EXPRESSION_LENGTH} characters"),
    ("'unclosed", "unclosed"),
    ("'a\\nb' + 1", "escapes are not supported"),
]


class TestHostileInput:
    @pytest.mark.parametrize(("text", "message"), HOSTILE)
    def test_rejected_in_palette(self, text: str, message: str) -> None:
        with pytest.raises(ThemeError, match=f"palette.x: .*{message}"):
            Palette({**LIGHT.palette.sources, "x": text})

    @pytest.mark.parametrize(("text", "message"), [h for h in HOSTILE if h[0] != "lambda: 0"])
    def test_rejected_in_roles_and_files(self, text: str, message: str) -> None:
        with pytest.raises(ThemeError, match=f"roles.probe.stroke-width: .*{message}"):
            role_value(text, "stroke-width")
        toml = f"[roles.probe]\nstroke-width = '''{text}'''\n"
        with pytest.raises(ThemeError, match=f"roles.probe.stroke-width: .*{message}"):
            svg.Theme.from_toml(toml)

    def test_other_text_is_written_as_text(self) -> None:
        assert role_value("lambda: 0", "content") == "lambda: 0"
        assert role_value("f{palette.primary}", "content") == f"f{LIGHT.palette.primary.hex}"

    def test_reference_cycles(self) -> None:
        with pytest.raises(ThemeError, match="cycle: palette.a -> palette.b -> palette.a"):
            Palette({"a": "lighten({palette.b}, 0.1)", "b": "mix({palette.a}, white)"})
        with pytest.raises(ThemeError, match="cycle: palette.a -> palette.a"):
            Palette({"a": "if(is_dark({palette.a}), black, white)"})

    def test_reference_chain_depth(self) -> None:
        def chain(length: int) -> dict[str, str]:
            links = {f"c{i}": f"darken({{palette.c{i + 1}}}, 0.01)" for i in range(length - 1)}
            return {**links, f"c{length - 1}": "white"}

        assert Palette(chain(MAX_REFERENCE_DEPTH)).c0.hex
        with pytest.raises(ThemeError, match=f"references nest deeper than {MAX_REFERENCE_DEPTH} levels"):
            Palette(chain(MAX_REFERENCE_DEPTH + 1))

    def test_long_text_rejected(self) -> None:
        with pytest.raises(ThemeError, match="longer than"):
            role_value("a" * (MAX_EXPRESSION_LENGTH + 1), "font-family")


@pytest.mark.parametrize(("expression", "message"), [
    ("lighten(red)", r"lighten\(\) takes 2 arguments, got 1"),
    ("mix(red, blue, 0.5, 'hsl', 1)", r"mix\(\) takes 2 to 4 arguments, got 5"),
    ("lighten(red, 2)", "argument 2 must be between 0 and 1"),
    ("lighten(3, 0.5)", "argument 1 must be a color, got number"),
    ("lighten('nope', 0.5)", "argument 1 must be a color, got text"),
    ("mix(red, blue, 0.5, 3)", "argument 4 must be text"),
    ("mix(red, blue, 0.5, 'hsl')", "unknown mixing space"),
    ("round(1.5, 0.5)", "whole number"),
    ("clamp(1, 3, 2)", "lower bound 3 is above the upper bound 2"),
    ("max(1, red)", "argument 2 must be a number, got color"),
    ("red + 1", r"\+ needs numbers, got color"),
    ("1 / 0", "division by zero"),
    ("red == 1", "cannot compare color with number"),
    ("1 < 'a'", "< needs numbers, got text"),
    ("1 < 2 < 3", "comparisons cannot be chained"),
    ("1 and true", "and needs conditions, got number"),
    ("not 'a'", "not needs conditions, got text"),
    ("if(1, 2, 3)", r"if\(\) needs conditions, got number"),
    ("nope(1)", "unknown function 'nope'"),
    ("nope * 2", "unknown name 'nope'"),
    ("lighten(#12345, 0.1)", "unknown color '#12345'"),
    ("rgb(1, 2", "unclosed color function"),
    ("2em * 2", "unit 'em' is not supported"),
    ("{palette}", "malformed reference"),
    ("{other.x} * 2", "unknown reference"),
    ("{fonts.sizes.nope} * 2", "unknown reference"),
    ("{fonts.sizes.text} *", "unexpected end of expression"),
    ("(1, 2)", "unexpected ','"),
    ("(1 ; 2)", "unexpected character ';'"),
])
def test_errors_name_the_key(expression: str, message: str) -> None:
    with pytest.raises(ThemeError, match=f"^roles.probe.stroke-width: .*{message}"):
        role_value(expression, "stroke-width")


def test_condition_is_not_a_css_value() -> None:
    with pytest.raises(ThemeError, match="a condition is not a CSS value"):
        role_value("1 < 2")


def test_errors_name_the_file(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text('[palette]\naccent = "lighten({palette.primary}, 5)"\n', encoding="utf-8")
    with pytest.raises(ThemeError, match=r"bad\.toml: palette\.accent: lighten\(\): argument 2"):
        svg.Theme.load(path)

"""Wide-gamut colours in theme palettes, theme expressions and gradients, through PNG and PDF."""

import io

import pytest

import svgwriter as svg

GREEN = "oklch(0.7 0.3 145)"
P3_RED = "color(display-p3 1 0 0)"


def theme() -> svg.Theme:
    return svg.Theme.get("light").replace(palette={
        "primary": "oklch(0.7 0.25 30)",
        "accent": P3_RED,
        "blend": lambda p: p.primary.mix(p.accent, space="oklch"),
    }, roles={"blend": {"fill": "{palette.blend}"}})


def drawing() -> svg.Document:
    doc = svg.Document(90, 30, theme=theme())
    doc.rect(0, 0, 30, 30, fill=svg.LinearGradient.horizontal(GREEN, GREEN))
    doc.rect(30, 0, 30, 30).as_role("shape")
    doc.rect(60, 0, 30, 30).as_role("blend")
    return doc


def test_mix_in_oklch_from_python_and_toml_agree():
    python = theme().palette.blend
    toml = svg.Theme.from_toml('name = "w"\nextends = "light"\n[palette]\nprimary = "oklch(0.7 0.25 30)"\n'
                               f'accent = "{P3_RED}"\nblend = "=mix({{palette.primary}}, {{palette.accent}}, 0.5, \'oklch\')"\n')
    assert toml.palette.blend.hex == python.hex
    assert python.hex != theme().palette.primary.mix(theme().palette.accent).hex


@pytest.mark.parametrize("icc", [None, "display-p3"])
def test_png_paints_every_wide_gamut_colour(icc):
    image = pytest.importorskip("PIL.Image")
    options = {} if icc is None else {"icc": icc}
    pixels = image.open(io.BytesIO(drawing().export("png", **options))).convert("RGB")
    green, primary, blend = (pixels.getpixel((x, 15)) for x in (15, 45, 75))
    assert green[1] > 150 and green[0] < 120 and green[2] < 120
    assert primary[0] > 200 and primary[1] < 120
    assert blend[0] > 200 and blend != primary
    if icc is not None:
        assert "icc_profile" in image.open(io.BytesIO(drawing().export("png", **options))).info


def test_pdf_paints_wide_gamut_colours_not_black():
    doc = drawing()
    doc.rect(0, 0, 10, 10, fill=GREEN)
    pdf = svg.Document.from_string(doc.export("pdf"), "pdf")
    fills = [str(path.get("fill")).lower() for path in pdf.root.iter("path")]
    assert fills[-1] == svg.Color.parse(GREEN).hex
    assert "#000000" not in fills and "black" not in fills

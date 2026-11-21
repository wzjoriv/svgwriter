from __future__ import annotations

import base64
import io
import re

import pytest
import skia

import svgwriter as svg
from svgwriter._internal import _fonts

EM = 1000
REGULAR, BOLD = 400, 700


def _font(family: str, width: int = 400, *, weight: int = REGULAR, italic: bool = False, width_class: int = 5,
          variable: bool = False) -> bytes:
    """A one-glyph TrueType font whose 'A' is a box *width* units wide (advance = width + 100)."""
    builder = pytest.importorskip("fontTools.fontBuilder")
    pens = pytest.importorskip("fontTools.pens.ttGlyphPen")
    fb = builder.FontBuilder(EM, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({ord("A"): "A"})
    pen = pens.TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 700))
    pen.lineTo((width, 700))
    pen.lineTo((width, 0))
    pen.closePath()
    fb.setupGlyf({".notdef": pens.TTGlyphPen(None).glyph(), "A": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (width + 100, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": family, "styleName": "Italic" if italic else "Regular"})
    fb.setupOS2(usWeightClass=weight, usWidthClass=width_class, fsSelection=1 if italic else 0x40,
                sxHeight=500, sCapHeight=700)
    fb.updateHead(macStyle=2 if italic else 0)
    fb.setupPost()
    if variable:
        fb.setupFvar([("wght", 100, 400, 900, "Weight"), ("wdth", 75, 100, 100, "Width"),
                      ("slnt", -12, 0, 0, "Slant")], [])
        fb.setupGvar({})
    buffer = io.BytesIO()
    fb.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def family(tmp_path):
    """A three-face family on disk: regular (A = 400 wide), bold (600) and italic (500)."""
    files = {"regular": (400, {}), "bold": (600, {"weight": BOLD}), "italic": (500, {"italic": True})}
    paths = []
    for name, (width, options) in files.items():
        path = tmp_path / f"Probe-{name}.ttf"
        path.write_bytes(_font("SvgwProbe", width, **options))
        paths.append(path)
    return paths


def test_from_files_reads_each_face_from_its_file(family):
    typeface = svg.Typeface.from_files(*family)
    assert typeface.name == "SvgwProbe" and len(typeface) == 3
    assert [(face.weight, face.style, face.stretch) for face in typeface] == [
        ((400, 400), "normal", (100, 100)), ((700, 700), "normal", (100, 100)), ((400, 400), "italic", (100, 100))]
    assert typeface.faces[0].source == family[0] and not typeface.installed


@pytest.mark.parametrize(("weight", "style", "expected"), [
    (400, "normal", (400, "normal")), (450, "normal", (400, "normal")), (600, "normal", (700, "normal")),
    (900, "normal", (700, "normal")), (100, "normal", (400, "normal")), ("bold", "normal", (700, "normal")),
    (700, "italic", (400, "italic")), (400, "oblique", (400, "italic")), (400, True, (400, "italic")),
])
def test_face_follows_css_font_matching(family, weight, style, expected):
    face = svg.Typeface.from_files(*family, name="SvgwMatch").face(weight, style)
    assert (face.weight[0], face.style) == expected


def test_weights_between_400_and_500_look_up_to_500_first(tmp_path):
    sources = [_font("SvgwSpan", weight=weight) for weight in (300, 500, 600)]
    typeface = svg.Typeface.from_files(*sources)
    assert typeface.face(420).weight[0] == 500
    assert typeface.face(350).weight[0] == 300
    assert typeface.face(550).weight[0] == 600


def test_text_renders_with_the_face_for_its_weight_and_style(family):
    typeface = svg.Typeface.from_files(*family, name="SvgwRender")
    widths = [svg.text("A", x=0, y=100, font_size=100, font_family=typeface, **style).to_path().exact_bbox().width
              for style in ({}, {"font_weight": "bold"}, {"font_style": "italic"}, {"font_weight": 600})]
    assert widths == pytest.approx([40, 60, 50, 60], abs=0.5)


def test_font_keyword_sets_the_family():
    typeface = svg.Typeface("serif")
    label = svg.text("Hi", x=0, y=10, font=typeface)
    assert "font" not in label.attributes and label.computed("font_family") == str(typeface)
    assert f'font-family="{typeface}"' in svg.Svg(label).to_string()


def test_measure_uses_the_shaped_advance(family):
    typeface = svg.Typeface.from_files(*family, name="SvgwMeasure")
    assert typeface.measure("AA", 100) == pytest.approx(100)
    assert typeface.measure("AA", 100, weight=BOLD) == pytest.approx(140)
    assert typeface.face(style="italic").measure("A", 50) == pytest.approx(30)


def test_metrics_come_from_the_font(family):
    metrics = svg.Typeface.from_files(*family, name="SvgwMetrics").face().metrics
    assert metrics == svg.ops.FaceMetrics(EM, 800, 200, 500, 700)
    assert metrics.at(20).x_height == pytest.approx(10)


def test_mapping_overrides_what_the_file_says(family):
    typeface = svg.Typeface("SvgwOverride", {(REGULAR, "normal"): family[0], (900, "italic"): family[1]})
    assert typeface.face(900, "italic").source == family[1]
    extra = svg.Typeface.from_files(family[0], name="SvgwExtra", faces={(300, "normal"): family[2]})
    assert extra.face(300).source == family[2]


def test_variable_fonts_expose_their_axes_and_pin_instances():
    typeface = svg.Typeface.from_files(_font("SvgwFlex", variable=True))
    face = typeface.faces[0]
    assert face.variable and face.weight == (100, 900) and face.stretch == (75, 100)
    assert face.axes["wght"] == (100, 400, 900) and face.styles == {"normal", "oblique"}
    assert typeface.face(650).weight == (650, 650)
    instance = _fonts.resolve_font("SvgwFlex", 16, 650, True).getTypeface()
    position = {coordinate.axis: coordinate.value for coordinate in instance.getVariationDesignPosition()}
    assert position[int.from_bytes(b"wght", "big")] == 650 and position[int.from_bytes(b"slnt", "big")] == -12


def test_register_font_takes_weight_and_style_descriptors():
    svg.register_font(_font("SvgwLow", 300), weight=BOLD, style="italic")
    svg.register_font(_font("SvgwLow", 500))
    assert _fonts.resolve_font("SvgwLow", 100, BOLD, True).measureText("A") == pytest.approx(40)
    assert _fonts.resolve_font("SvgwLow", 100, REGULAR, False).measureText("A") == pytest.approx(60)


def test_css_embeds_the_file_with_its_descriptors(family):
    typeface = svg.Typeface.from_files(_font("SvgwCss", variable=True), *family[1:], name="SvgwCss")
    rules = typeface.css().splitlines()
    assert len(rules) == 3 and 'font-family: "SvgwCss"' in rules[0]
    assert "font-weight: 100 900" in rules[0] and "font-stretch: 75% 100%" in rules[0]
    assert "font-style: italic" in rules[2] and 'format("truetype")' in rules[1]
    data = base64.b64decode(re.search(r"base64,([^)]+)\)", rules[1]).group(1))
    assert data == family[1].read_bytes()


def test_embed_fonts_writes_only_the_used_faces(family):
    typeface = svg.Typeface.from_files(*family, name="SvgwEmbed")
    doc = svg.Document(100, 100)
    assert doc.embed_fonts(typeface) is None
    doc.text("A", x=0, y=40, font_family=typeface, font_weight="bold")
    doc.text("A", x=0, y=80, font_family=f"{typeface}, serif", font_weight=800)
    doc.style(".note { font-family: SvgwEmbed; font-style: italic }")
    doc.text("A", x=0, y=90, class_="note")
    assert [(face.weight[0], face.style) for face in doc.used_faces(typeface)] == [(700, "normal"), (400, "italic")]
    style = doc.embed_fonts()
    assert style.css.count("@font-face") == 2
    assert svg.Document.from_string(doc.to_string()).render_png()


def test_embed_fonts_sees_theme_roles(family):
    typeface = svg.Typeface.from_files(*family, name="SvgwRole")
    doc = svg.Document(100, 40)
    doc.theme = svg.Theme.get("light").replace(fonts={"family": typeface})
    doc.text("A", x=0, y=30).as_role("title")
    assert [face.weight[0] for face in doc.used_faces(typeface)] == [BOLD]


def test_from_folder_takes_one_family(tmp_path, family):
    (tmp_path / "Other.ttf").write_bytes(_font("SvgwOther"))
    with pytest.raises(ValueError, match="several families"):
        svg.Typeface.from_folder(tmp_path)
    assert len(svg.Typeface.from_folder(tmp_path, "SvgwProbe")) == 3
    assert svg.Typeface.from_folder(tmp_path, "svgwother").name == "SvgwOther"
    with pytest.raises(ValueError, match="no Missing files"):
        svg.Typeface.from_folder(tmp_path, "Missing")


def test_installed_families_and_errors():
    serif = svg.Typeface("serif")
    assert serif.installed and len(serif) >= 1 and serif.name != "serif"
    rebuilt = skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(serif.face().data))
    assert rebuilt.getFamilyName() == serif.face().typeface.getFamilyName()
    with pytest.raises(LookupError, match="no installed font family"):
        svg.Typeface("Svgw No Such Family")
    with pytest.raises(ValueError, match="font"):
        svg.Typeface.from_files(b"not a font")
    with pytest.raises(ValueError, match="at least one"):
        svg.Typeface.from_files()


def test_family_names_are_quoted_when_css_needs_it():
    typeface = svg.Typeface.from_files(_font("Svgw 2 Faces"))
    assert str(typeface) == "'Svgw 2 Faces'"
    assert svg.ops.text_width("A", str(typeface), 100) == pytest.approx(50)


def test_theme_files_accept_font_files(tmp_path, family):
    path = tmp_path / "brand.toml"
    path.write_text(f'name = "brand"\n[fonts]\nfamily = ["{family[0].name}", "{family[1].name}"]\n',
                    encoding="utf-8")
    theme = svg.Theme.load(path)
    assert isinstance(theme.fonts.family, svg.Typeface) and len(theme.fonts.family) == 2
    assert theme.fonts.lookup("family") == "SvgwProbe"
    assert f'family = ["{family[0].name}", "{family[1].name}"]' in theme.to_toml()
    assert theme.fonts.to_dict()["family"] == [str(family[0]), str(family[1])]
    with pytest.raises(svg.theme.ThemeError, match="fonts.family"):
        svg.Theme.from_toml('[fonts]\nfamily = ["missing.ttf"]\n')


def _named(legacy: str, subfamily: str, weight: int, width: int, *, italic: bool = False) -> bytes:
    """A face whose legacy name (ID 1) differs from its typographic family (ID 16), as non-RIBBI styles do."""
    ttlib = pytest.importorskip("fontTools.ttLib")
    font = ttlib.TTFont(io.BytesIO(_font("unused", width, weight=weight, italic=italic)))
    names = font["name"]
    names.names = []
    names.setName(legacy, 1, 3, 1, 0x409)
    names.setName("Italic" if italic else "Regular", 2, 3, 1, 0x409)
    names.setName("SvgwInterish", 16, 3, 1, 0x409)
    names.setName(subfamily, 17, 3, 1, 0x409)
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def test_typographic_names_keep_a_large_family_together(tmp_path):
    faces = {"Regular.ttf": ("SvgwInterish", "Regular", 400, 400, False),
             "SemiBold.ttf": ("SvgwInterish SemiBold", "SemiBold", 600, 550, False),
             "SemiBoldItalic.ttf": ("SvgwInterish SemiBold", "SemiBold Italic", 600, 560, True)}
    for file, (legacy, subfamily, weight, width, italic) in faces.items():
        (tmp_path / file).write_bytes(_named(legacy, subfamily, weight, width, italic=italic))
    typeface = svg.Typeface.from_folder(tmp_path)
    assert typeface.name == "SvgwInterish" and len(typeface) == 3
    semibold = typeface.face(600)
    assert semibold.weight == (600, 600) and semibold.subfamily == "SemiBold"
    assert typeface.face(600, "italic").subfamily == "SemiBold Italic"
    assert svg.register_font(_named("SvgwInterish Light", "Light", 300, 300)) == "SvgwInterish"


def test_collections_load_every_face():
    collection = pytest.importorskip("fontTools.ttLib.ttCollection")
    ttlib = pytest.importorskip("fontTools.ttLib")
    bundle = collection.TTCollection()
    bundle.fonts = [ttlib.TTFont(io.BytesIO(_font("SvgwBundle", 400))),
                    ttlib.TTFont(io.BytesIO(_font("SvgwBundle", 600, weight=BOLD)))]
    buffer = io.BytesIO()
    bundle.save(buffer)
    typeface = svg.Typeface.from_files(buffer.getvalue())
    assert [face.weight[0] for face in typeface] == [REGULAR, BOLD]
    assert typeface.measure("A", 100, weight=BOLD) == pytest.approx(70)
    single = skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(typeface.face(BOLD).data))
    assert single.fontStyle().weight() == BOLD
    from svgwriter._internal._sfnt import collection_member

    member = skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(collection_member(buffer.getvalue(), 1)))
    assert member.fontStyle().weight() == BOLD


def test_sources_may_be_streams_and_data_uris():
    data = _font("SvgwStream", 300)
    uri = "data:font/ttf;base64," + base64.b64encode(data).decode("ascii")
    typeface = svg.Typeface.from_files(io.BytesIO(data), name="SvgwStream")
    assert svg.Typeface.from_files(uri).name == "SvgwStream" and len(typeface) == 1


def test_css_can_reference_instead_of_embed(family):
    typeface = svg.Typeface.from_files(*family, name="SvgwLinked")
    assert f'url("{family[0].as_posix()}")' in typeface.css(embed=False) and "base64" not in typeface.css(embed=False)
    serif = svg.Typeface("serif")
    assert f"local('{serif.name} {serif.face().subfamily}')" in serif.css([serif.face()], embed=False)


def test_unknown_installed_family_suggests_close_names(monkeypatch: pytest.MonkeyPatch):
    from svgwriter.ops import _sources

    monkeypatch.setattr(_sources, "_installed_families", lambda: ("Gill Sans", "Georgia", "Helvetica"))
    with pytest.raises(LookupError, match="did you mean 'Georgia'"):
        svg.Typeface("georgai")

# Making fonts

`svg.FontBuilder` turns drawings into a font: letters from paths, strokes or text outlines, icons on
private-use code points, kerning pairs, and files in OpenType (`.otf`), TrueType (`.ttf`) and web formats
(`.woff`, `.woff2`). Compiling needs the `fonts` extra:

```bash
pip install 'pysvgwriter[fonts]'
```

## Letters

```python
import svgwriter as svg

fb = svg.FontBuilder(family="My Hand", style="Regular", weight=400, scale=10)
pen = {"fill": "none", "stroke": "black", "stroke_width": 7, "stroke_linecap": "round"}
fb.glyph("l", svg.path("M5 -70 C3 -40 3 -15 10 0", **pen), left=60, right=60)
fb.glyph("o", svg.circle(17, -20, 17, **pen), left=60, right=60)
fb.glyph(" ", advance=300)
fb.kern("l", "o", -30)
fb.save("MyHand.otf")
```

The coordinate convention follows svgwriter, not the font file:

- Drawings keep y pointing down. The drawing's `y=0` is the baseline, so letters sit at negative y and
  descenders reach positive y. `baseline=` moves it, for a drawing made elsewhere.
- One drawing unit is `scale` font units (builder-wide, or per glyph with `scale=`). A font has
  `units_per_em` units per em (1000 by default), with `ascent` above the baseline and `descent` below it.
- The outline is shifted so its left edge sits `left` units after the glyph origin. The advance width
  defaults to the outline's width plus `left` and `right`; `advance=` sets it outright, and an empty glyph
  such as a space needs it.
- Fills and strokes both become outline (a stroke turns into the area it paints, with its caps and
  joins), groups merge their children, and overlaps are removed, so hand-drawn strokes may cross freely.
  Text works too: `svg.text("Ж", font_size=1000)` brings a glyph from another font.

`cap_height=`, `x_height=` and `line_gap=` fill the font's metrics. `fb.kern(left, right, value)` takes
characters or icon names; negative values pull the pair together.

## Using the font at once

```python
hand = fb.typeface()                                  # svg.Typeface.from_files(fb.to_bytes(".otf"))
doc = svg.Document(400, 100)
doc.text("hello", x=20, y=70, font_family=hand, font_size=64)
doc.embed_fonts()                                     # the SVG carries the font
```

`fb.to_bytes(".ttf")` returns the file's content without writing it.

## Formats

The suffix picks the format:

| Suffix | Outlines | Notes |
|---|---|---|
| `.otf` | cubic (CFF) | drawn curves are kept exactly |
| `.ttf` | quadratic (TrueType) | cubic curves are converted within one font unit |
| `.woff` | cubic (CFF) | zlib-compressed web font |
| `.woff2` | cubic (CFF) | Brotli-compressed web font; needs `brotli` (part of the extra) |

## Icon fonts

```python
icons = svg.FontBuilder(family="Icons")
icons.icon("rocket", svg.path("M12 2 C16 5 17 10 16 16 H8 C7 10 8 5 12 2 Z"))
icons.icon("star", svg.builder.star(12, 12, 10))
icons.save("Icons.woff")                             # .woff2 with brotli installed
icons.save_css("icons.css", font="Icons.woff")
icons.cheatsheet().save("icons.svg")
```

Each icon gets the next private-use code point from U+E000 in the order it is added, and adding a name
again keeps its code point, so pages that use the font stay valid. The drawing may use any coordinates: it
is scaled to fit the em (ascent plus descent, or `size=`) and centered in a square advance. `icon()` returns
the character, and `icons.icons` maps every name to its character.

`save_css` writes an `@font-face` rule and one class per icon:

```css
.icon-rocket::before { content: "\e000"; }
```

so `<i class="icon-rocket"></i>` shows the rocket; `prefix=` changes `icon`. `css()` returns the same text.
`cheatsheet(columns=)` returns a document with every glyph drawn with its name and code point.

`examples/20_fonts.py` in the repository builds a small handwritten alphabet and a four-icon font with its
stylesheet and cheatsheet.

## Limits

Glyphs are single outlines without hinting, color layers or variable axes; kerning is pair kerning
(no classes or contextual features).

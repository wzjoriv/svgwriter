# Text

## Text, runs and styles

```python
import svgwriter as svg

doc = svg.Document(300, 80)
title = doc.text("Hello ", x=10, y=50, font_size=32, font_family="Georgia, serif")
title.span("world", fill="crimson", font_weight="bold")
print(title.characters)          # 'Hello world'
```

Fonts come from the computed style: attributes on the text and its `tspan`s, inherited values from
ancestors, and CSS from `<style>` elements all apply, as in a browser. Whitespace follows SVG's
`xml:space` rules.

## Characters as handles

`text[i]` is a live {class}`~svgwriter.elements.text.Glyph` and `text[a:b]` a `GlyphRange`. Moving and
rotating them edits SVG's per-character `dx`/`dy`/`rotate` lists, so the result is still real,
selectable text:

```python
t = doc.text("wavy text", x=10, y=40, font_size=24)
for i, glyph in enumerate(t):
    glyph.translate(0, (-1) ** i * 3)
t[5:].rotate(-10)
print(len(t), t[0].char, t[0].position)
```

Setting a presentation attribute on a range wraps it in a `<tspan>`:

```python
note = svg.text("Status: OK", x=0, y=20)
note[8:].fill = "green"
note[0:6].wrap(font_weight="bold")
print(note)
```

Scaling or skewing one character has no SVG text form; those calls raise and point to
`text.glyphs()`, which returns one outline `<path>` per character, styled like its run:

```python
outlines = svg.text("BIG", x=0, y=40, font_size=40).glyphs()
outlines[1].scale(1.5)
```

## Outlines and measurement

```python
word = svg.text("Outline", x=0, y=40, font_size=36)
path = word.to_path()                       # glyph outlines as a <path>
print(word.exact_bbox())
print(svg.ops.text_width("Outline", "sans-serif", 36))
```

Text takes part in boolean operations (`rect - text`) and clipping (`art.clip(text)`) through its
outlines.

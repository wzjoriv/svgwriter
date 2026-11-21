# Rendering

svgwriter renders with skia and returns numpy arrays.

```python
import svgwriter as svg

doc = svg.Document(200, 100)
doc.circle(100, 50, 40, fill="teal")

pixels = doc.rasterize()                          # float32 RGBA in 0..1, shape (100, 200, 4)
hires = doc.rasterize(scale=4)                    # (400, 800, 4)
thumb = doc.rasterize(size=(64, 64), padding=10)  # exact size, drawing fitted and centred
flat = doc.rasterize(background="white")
png = doc.render_png(scale=2)
```

Single elements render on their own, over their stroke-inclusive bounds:

```python
star = svg.builder.star(0, 0, 20, fill="gold", stroke="black")
print(star.rasterize(scale=2, padding=2).shape)
```

## What the renderer handles

skia's SVG renderer does not load images, draw text or apply `<style>` sheets. svgwriter renders a working
copy of the document in which:

- CSS rules are resolved into attributes,
- every `<text>` is drawn as glyph outlines, one path per styled run,
- embedded images, and images linked to local files (resolved against the document's file and
  `xml:base`), are drawn in paint order with their transforms, aspect ratio, opacity and clip.

The document you pass is never modified. Output is deterministic: the same document gives the same
pixels and the same file bytes.

## Fonts

Text uses installed fonts through skia. `font-family` may list fallbacks (`"Inter, Arial, sans-serif"`);
the first installed family wins and a warning names the substitute when none is found.

## Many documents at once

skia holds Python's global lock, so threads do not speed up rendering; processes do.
`svgwriter.ops.rasterize_many(documents, processes=None, dtype="uint8")` renders a batch in worker
processes (each document travels as SVG text) and returns the arrays in order. Animated exports take
`processes=` too: `doc.save("clip.gif", processes=None)`. Pools start in about a second, so they pay off
for batches of a few dozen non-trivial drawings; scripts on Windows and macOS need the usual
`if __name__ == "__main__":` guard.


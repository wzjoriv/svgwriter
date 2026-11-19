# Colors and images

## Colors

Colors are {class}`~svgwriter.Color` values with red, green, blue and alpha as floats in `0..1`
(as in matplotlib). Anything that takes a color also takes a name, CSS text or a 3/4-tuple or array:

```python
import svgwriter as svg

svg.rect(fill="tomato")
svg.rect(fill="#ff6347cc")
svg.rect(fill="rgba(255, 99, 71, 0.8)")
svg.rect(fill=(1.0, 0.39, 0.28, 0.8))
c = svg.Color.from_uint8(255, 99, 71)          # 0..255 values are explicit
print(c.hex, c.rgba, c.uint8)
print(c.lighten(0.2).hex, c.mix("navy").hex, (c * 0.5).hex)
```

Tuples are always `0..1`; a value above 1 raises and points to `Color.from_uint8`. SVG 1.1 has no alpha
in colors, so a translucent `fill`, `stroke`, `stop-color` or `flood-color` also writes the matching
`*-opacity` attribute:

```python
print(svg.rect(fill=(1, 0, 0, 0.5)))     # fill="#ff0000" fill-opacity="0.5"
```

## Images are numpy arrays

`svg.Image(array)` embeds pixels. They are stored as `color`, a float32 `(H, W, 3)` array (or
`(H, W, 1)` for grayscale) in `0..1`, and `alpha`, which is the scalar `1.0` when the image is opaque or
an `(H, W, 1)` array, so `color * alpha` always broadcasts.

```python
import numpy as np

y, x = np.mgrid[0:64, 0:64] / 63
img = svg.Image(np.dstack([x, y, 1 - x]), 10, 10, 80, 80)        # floats 0..1
img.alpha = np.clip(1.4 - 2 * np.hypot(x - 0.5, y - 0.5), 0, 1)  # (H, W) broadcasts
img.color[..., 0] *= 0.5                                         # edit in place
print(img.shape, img.color.dtype, img.alpha.shape)
data = img.encode("png")
```

uint8 arrays are divided by 255. `Image.open("photo.jpg")` decodes a file; `Image("photo.jpg", ...)`
links to it instead (linked local files are drawn when rendering). Images are written as PNG `data:` URIs.

Any element can become an image: `el.to_image(scale=2)` rasterizes it and places the result where the
element was.

## Compositing images

The boolean operators that combine shape areas combine image coverage too, using the Porter-Duff
operators of `feComposite`: `a | b` is *a* over *b*, `a & b` keeps *a* where *b* is opaque, `a - b`
keeps *a* where *b* is not, and `a ^ b` keeps whatever is not shared. `a * b` is the multiply blend.
`a.composite(b, operator)` takes any `feComposite` operator or `feBlend` mode by name: `"over"`, `"in"`,
`"out"`, `"atop"`, `"xor"`, `"arithmetic"` (with `k=(k1, k2, k3, k4)`), `"multiply"`, `"screen"`,
`"darken"`, `"lighten"`.

```python
photo = svg.Image(np.dstack([x, y, 1 - x]))                 # 64 x 64
badge = photo & svg.circle(32, 32, 32)                      # masked by a shape
shadow = svg.Image(np.zeros((64, 64)), 4, 4, alpha=0.4)
card = badge | shadow                                       # over, on the union of both boxes
glow = photo.composite(shadow, "screen")
print(card.shape, (card.x, card.y, card.width))
```

Images with the same placement and pixel size combine pixel for pixel. Otherwise both are rendered onto
one canvas in parent coordinates (the union of their boxes, the source's box for `in` and `out`, the
backdrop's for `atop`) at the finer resolution of the two, or at `scale=`. The other operand can be any
drawable element, and numbers keep their transform meaning: `img * 2` scales and `img - (dx, dy)`
moves. `Pixels` offers the same operators pixel for pixel, and `svgwriter.ops.composite_rgba` works on
raw RGBA arrays that broadcast, so a `(1, 1, 4)` color composites onto a whole image.

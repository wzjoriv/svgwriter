# Geometry operations and rendering

Boolean operations, measurement, text outlines and rendering, backed by skia.

Font families live here too: `Typeface` (also `svg.Typeface`), its `Face` objects with `FaceMetrics`,
and the low-level `register_font`; see [Typography](../guides/text.md#typography). `Document.embed_fonts`
writes the faces a document uses as `@font-face` rules.

```{eval-rst}
.. automodule:: svgwriter.ops
   :members:
```

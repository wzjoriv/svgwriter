# Filters and effects

A filter is a small graph of `fe*` primitives. Each primitive reads an input (`in_=`, and `in2=` for
the two-input ones) and produces a result. Pass the primitive itself as an input and svgwriter names
the results for you; keywords such as `"SourceAlpha"` and `"SourceGraphic"` work too.

```python
import svgwriter as svg

blur = svg.FeGaussianBlur(3, in_="SourceAlpha")
shadow = svg.FeOffset(2, 2, in_=blur)
drop = svg.Filter(svg.FeMerge(shadow, "SourceGraphic"))   # blur and offset come along
print([p.tag for p in drop.primitives])

doc = svg.Document(80, 60)
doc.rect(10, 10, 50, 30, fill="gold", filter=drop)       # the filter lands in <defs>
```

`Filter(...)` collects every primitive its primitives read, in dependency order, so you only name the
last step. `a >> b` wires `b` to read `a` and returns `b`, which reads left to right:

```python
step = svg.FeGaussianBlur(2, in_="SourceAlpha") >> svg.FeOffset(3, 3)
glow = svg.Filter(svg.FeMerge(step, "SourceGraphic"))
```

SVG 1.1 gives an element a single `filter`, so effects stack by chaining whole filters: `f1 >> f2` is
one filter that applies `f1`, then `f2` to its result.

```python
soft = svg.Filter(svg.FeGaussianBlur(1))
stacked = soft >> drop
print(len(stacked.primitives))
```

Ready-made filters live in `svg.filters` (`drop_shadow`, `glow`, `long_shadow`, `outline`, `goo`, ...),
with patterns, gradients, markers and text effects beside them; see the [Presets guide](presets.md).

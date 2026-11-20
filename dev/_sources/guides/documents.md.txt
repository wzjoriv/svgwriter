# Documents

## Building

```python
import svgwriter as svg

doc = svg.Document(200, 100)
with doc.group(stroke="black", fill="gold") as g:     # shortcuts inside go into the group
    doc.circle(50, 50, 20)
    doc.rect(100, 30, 40, 40)
doc += svg.circle(170, 50, 10)                         # or add elements directly
doc += [svg.line(0, 99, 200, 99, stroke="gray")]
```

## Access

```python
doc.rect(0, 0, 10, 10, id="logo")
print(doc[0].tag, doc[-1].tag, len(doc))    # top-level content
print(doc["logo"])                          # any element by id
print("logo" in doc)
for element in doc:
    print(element.tag)
for element in doc.root.iter("circle"):     # the whole tree
    print(element.cx)
```

## Definitions

Gradients, clip paths, patterns, markers and filters go into `<defs>` as soon as something that
references them is in the document:

```python
fade = svg.LinearGradient.horizontal("white", "black")
doc.rect(0, 0, 200, 100, fill=fade)          # fade is now in doc.defs, with an id
doc.defs += svg.Symbol(id="spare")           # or add definitions explicitly
```

## Auto-size

A document created without a size takes it from its content whenever it is written, rendered or
displayed; `fit()` makes that permanent.

```python
sketch = svg.Document()
sketch.circle(100, 100, 30, stroke="black", stroke_width=4)
print(sketch.content_bounds())       # BBox(x=68.0, y=68.0, width=64.0, height=64.0)
sketch.fit(padding=10)
```

## Other libraries

Anything with `_repr_svg_` (diagrams, formulas) or a matplotlib-style `savefig` can be added; it becomes
a `<g>` holding its `<svg>`, so it can be moved and scaled:

```python
class Badge:
    def _repr_svg_(self):
        return '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><circle cx="10" cy="10" r="9"/></svg>'

doc.add(Badge()).translate(150, 10).scale(0.5)
```

In Jupyter, documents display as SVG (`_repr_svg_`) and PNG (`_repr_png_`).

## Attributes

Every SVG attribute is readable and writable by its Python name. Unknown names raise with a suggestion;
custom attributes go through `attrs={...}`, `data_*` keywords or `el.set(name, value)`.

```python
r = svg.rect(0, 0, 10, 10, data_kind="tile")
r.stroke_linejoin = "round"
print(r.stroke_linejoin, r.width, r.computed("fill", "black"))
```

## Parsing and writing

```python
text = doc.to_string()
back = svg.Document.from_string(text)
doc.save("figure.svg", pretty=True, precision=3)
```

## Documents inside documents

A document has one outermost `<svg>`, its root. SVG allows further `<svg>` elements inside as their
own viewports, and `doc.add(other)` uses that: it adds a copy of the other document's `<svg>` (its size
and `viewBox` kept) inside a `<g>`, so the whole drawing moves and scales as one piece:

```python
icon = svg.Document(24, 24)
icon.circle(12, 12, 10, fill="teal")
sheet = svg.Document(200, 100)
sheet.add(icon).place(50, 50)        # a copy; later edits to icon do not change sheet
```

Explicit ids keep their values, so give embedded drawings distinct ids if they are referenced.

## Drawing your own objects

Give any class a `__svgwriter__(self)` method that returns an element, a document or anything else
`add` accepts, and `doc.add(obj)` and `group.add(obj)` draw it. A neural network, a graph or a circuit
can describe its own picture this way:

```python
class Network:
    def __init__(self, layers):
        self.layers = layers

    def __svgwriter__(self):
        picture = svg.group()
        for column, size in enumerate(self.layers):
            for row in range(size):
                picture.circle(20 + 60 * column, 20 + 25 * row, 8, fill="teal")
        return picture

doc = svg.Document(200, 150)
doc.add(Network([3, 5, 2]))
```

`add` also takes objects from other libraries: matplotlib figures (`savefig`), anything with
`_repr_svg_` (parsed into elements), anything with only `_repr_png_` or `_repr_jpeg_` (an `<image>`),
and numpy pixel arrays.

## Back into matplotlib

`svgwriter.ops.to_matplotlib(element_or_document, ax)` draws onto matplotlib axes as `PathPatch`
artists with their curves, colors, opacity and stroke widths, so svgwriter shapes can annotate plots
and stay editable there. With `doc.add(fig)` in the other direction, figures and drawings move both ways.

## Graphs

With the `pysvgwriter[graph]` extra, networkx graphs draw themselves: `doc.add(G)`, or
`svgwriter.ops.draw_graph(G, layout="circular", node_radius=8)` for options. Nodes are circles with
ids `node-<name>`, edges are lines (arcs when a directed edge runs both ways) with arrowheads for
directed graphs, and node or edge attributes (`fill`, `radius`, `label`, `stroke`, `width`) style
single items. Any networkx layout, a positions mapping or a layout function places the nodes.


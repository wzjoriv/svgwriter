# Document

The document, its shortcuts and its export entry points.

```{eval-rst}
.. autoclass:: svgwriter.Document
   :members:
   :inherited-members: ElementFactory
   :special-members: __getitem__, __iter__, __len__, __iadd__
```

## Named sizes

`Document(size="a4")`, `Scene.size` and project files take a name from `svg.SIZES`; `svgwriter sizes`
lists them. Paper and card sizes are in millimetres or inches, so the `viewBox` counts in those units;
screen sizes are pixels. Append `-landscape` or `-portrait` to any name to turn it.

```{eval-rst}
.. autodata:: svgwriter.SIZES
   :no-value:
.. autofunction:: svgwriter.page_size
.. autofunction:: svgwriter.register_size
.. autofunction:: svgwriter.unregister_size
```

# Elements

Element classes. Every class also has a lowercase alias (`svgwriter.circle` is `svgwriter.Circle`).

Each class lists its own members and links to its bases: moving, rotating, aligning and the
`center`/`top`/... attributes are on `Transformable`, which every shape, group, image and text inherits.

## Base classes

```{eval-rst}
.. autoclass:: svgwriter.model.elements.Element
   :members:
   :inherited-members: Composable

.. autoclass:: svgwriter.model.elements.Transformable
   :members:
   :inherited-members: Element

.. autoclass:: svgwriter.model.elements._behavior.Convertible
   :members:

.. autoclass:: svgwriter.model.elements.PathOperand
   :members:
```

## Shapes

```{eval-rst}
.. automodule:: svgwriter.model.elements.shapes
   :members:
```

## Structure and images

```{eval-rst}
.. automodule:: svgwriter.model.elements.structure
   :members:
```

## Text and fonts

```{eval-rst}
.. automodule:: svgwriter.model.elements.text
   :members:
```

## Paint servers, clipping and markers

```{eval-rst}
.. automodule:: svgwriter.model.elements.paint
   :members:
```

## Filters

```{eval-rst}
.. automodule:: svgwriter.model.elements.filters
   :members:
```

## Animation

```{eval-rst}
.. automodule:: svgwriter.model.elements.animation
   :members:
```

## Animation presets

`element.animate` returns a `Motion`; its methods add SMIL children and chain. `@svg.preset.animation`
adds presets of your own as more methods, and `Motion.apply` runs any animation function with typed
options (see [Preset functions](paths.md#preset-functions)).

```{eval-rst}
.. autoclass:: svgwriter.Motion
   :members:
```

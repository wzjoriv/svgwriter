# Elements

Element classes. Every class also has a lowercase alias (`svgwriter.circle` is `svgwriter.Circle`).

## Base classes

```{eval-rst}
.. autoclass:: svgwriter.elements.Element
   :members:
   :inherited-members: Composable

.. autoclass:: svgwriter.elements.Transformable
   :members:

.. autoclass:: svgwriter.elements._behavior.Convertible
   :members:

.. autoclass:: svgwriter.elements.PathOperand
   :members:
```

## Shapes

```{eval-rst}
.. automodule:: svgwriter.elements.shapes
   :members:
```

## Structure and images

```{eval-rst}
.. automodule:: svgwriter.elements.structure
   :members:
```

## Text and fonts

```{eval-rst}
.. automodule:: svgwriter.elements.text
   :members:
```

## Paint servers, clipping and markers

```{eval-rst}
.. automodule:: svgwriter.elements.paint
   :members:
```

## Filters

```{eval-rst}
.. automodule:: svgwriter.elements.filters
   :members:
```

## Animation

```{eval-rst}
.. automodule:: svgwriter.elements.animation
   :members:
```

## Animation presets

`element.animate` returns a `Motion`; its methods add SMIL children and chain. `@svg.preset.animation`
adds presets of your own as more methods, and `Motion.apply` runs any animation function with typed
options (see [Preset functions](builder.md#preset-functions)).

```{eval-rst}
.. autoclass:: svgwriter.Motion
   :members:
```

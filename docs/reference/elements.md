# Elements

Element classes. Every class also has a lowercase alias (`svgwriter.circle` is `svgwriter.Circle`).

## Base classes

```{eval-rst}
.. autoclass:: svgwriter.elements.Element
   :members:
   :inherited-members: Composable

.. autoclass:: svgwriter.elements.Transformable
   :members:

.. autoclass:: svgwriter.elements._convert.Convertible
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

## Text

```{eval-rst}
.. automodule:: svgwriter.elements.text
   :members:

.. autoclass:: svgwriter.elements._character.Character
   :members:

.. autoclass:: svgwriter.elements._character.CharacterRange
   :members:
```

## Paint servers, clipping and markers

```{eval-rst}
.. automodule:: svgwriter.elements.paint
   :members:

.. automodule:: svgwriter.elements.clip
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

# Units

Lengths, angles and quantities, and the unit factories `svg.mm`, `svg.inch`, `svg.deg`, ... A unit on
its own is one of itself (`height=svg.inch`). Units SVG has no suffix for (metres, feet, miles, ...)
are written in the nearest SVG unit.

```{eval-rst}
.. automodule:: svgwriter.model.units
   :members: length, angle, LengthUnit, AngleUnit

.. automodule:: svgwriter.model.units.length
   :members: Length, Unit

.. automodule:: svgwriter.model.units.angle
   :members: Angle

.. automodule:: svgwriter.model.units.quantity
   :members: Quantity, dimension_name
```

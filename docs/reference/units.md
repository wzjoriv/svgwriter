# Units

Lengths, angles and quantities, and the unit factories `svg.mm`, `svg.inch`, `svg.deg`, ... A unit on
its own is one of itself (`height=svg.inch`). Units SVG has no suffix for (metres, feet, miles, ...)
are written in the nearest SVG unit.

```{eval-rst}
.. automodule:: svgwriter.model.units
   :members: length, angle, LengthUnit, AngleUnit

.. automodule:: svgwriter.model.units.lengths
   :members: Length, Unit

.. automodule:: svgwriter.model.units.angles
   :members: Angle

.. automodule:: svgwriter.model.units.quantities
   :members: Quantity, dimension_name
```

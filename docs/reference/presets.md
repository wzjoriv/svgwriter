# Preset libraries

Ready-made patterns, gradients, filters, markers and effects; see the [Presets guide](../guides/presets.md)
for pictures of each. `@svg.preset.pattern`, `filter`, `gradient`, `marker` and `effect` (documented
under [Composite shapes and effects](builder.md)) add your own to these catalogues.

```{eval-rst}
.. automodule:: svgwriter.catalog.patterns
   :members:

.. automodule:: svgwriter.catalog.gradients
   :members:

.. automodule:: svgwriter.catalog.filters
   :members:

.. automodule:: svgwriter.catalog.markers
   :members:

.. automodule:: svgwriter.catalog.effects
   :members:
```

## Registries

Every registry (the preset kinds, `svg.themes`, `svg.FORMATS`, `svg.renderers`, `svg.project.presets` and
the command line's `commands`) is a `Registry`; see [Extending svgwriter](../guides/extending.md).

```{eval-rst}
.. autoclass:: svgwriter.Registry
   :members: register, list, get, unregister, find

```
